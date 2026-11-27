"""Ordered converter choices independent of Tk, FFmpeg detection or AI runtimes."""
from dataclasses import dataclass
import math

HEIGHTS=(360,540,720,1080,2160)
FAMILIES=(('h264','H.264','compatible','libx264'),('hevc','H.265','smaller','libx265'),('av1','AV1','smallest','libsvtav1'))

@dataclass(frozen=True)
class ConversionProfile:
    id:str
    label:str
    family:str|None
    extension:str
    height:int|None
    arguments:tuple[str,...]

def _arguments(family,encoder,extension):
    values=['-map','0:v:0','-map','0:a?','-map_metadata','0','-c:v',encoder,'-preset','8' if family=='av1' else 'medium','-crf','{crf}','-pix_fmt','yuv420p']
    if extension=='.mp4' and family=='hevc':values+=['-tag:v','hvc1']
    values+=['-c:a','libopus' if family=='av1' and extension=='.mkv' else 'aac','-b:a','128k' if family=='av1' else '192k']
    if extension=='.mp4':values+=['-movflags','+faststart']
    return tuple(values)

def visible_profiles():
    profiles=[]
    for height in (*HEIGHTS,None):
        for family,name,description,encoder in FAMILIES:
            for extension in ('.mp4','.mkv'):
                label=f"{str(height)+'p' if height else 'Keep source'} {name} {extension[1:].upper()} ({description})"
                profiles.append(ConversionProfile(label,label,family,extension,height,_arguments(family,encoder,extension)))
    for extension in ('.mp4','.mkv'):
        label=f'Remux to {extension[1:].upper()} (no re-encoding)'
        args=('-map','0','-map_metadata','0','-c','copy')+(('-movflags','+faststart') if extension=='.mp4' else ())
        profiles.append(ConversionProfile(label,label,None,extension,None,args))
    return tuple(profiles)

PROFILES={p.id:p for p in visible_profiles()}
ALIASES={'H.264 MP4 (compatible)':'Keep source H.264 MP4 (compatible)','H.265 MP4 (smaller)':'Keep source H.265 MP4 (smaller)','AV1 MKV (smallest)':'Keep source AV1 MKV (smallest)','H.264 MKV':'Keep source H.264 MKV (compatible)','H.265 MKV':'Keep source H.265 MKV (smaller)','720p H.264 proxy':'720p H.264 MP4 (compatible)'}

def profile_for_id(preset_id):
    try:return PROFILES[ALIASES.get(preset_id,preset_id)]
    except KeyError:raise ValueError(f'Unknown conversion preset: {preset_id}') from None

def output_dimensions(width,height,target_height,rotation=0,sar=(1,1)):
    if min(width,height,*sar)<=0:raise ValueError('Unknown source dimensions')
    width=width*sar[0]/sar[1]
    if rotation%180:width,height=height,width
    final_height=target_height or max(2,round(height/2)*2)
    return max(2,math.floor(width/height*final_height/2+.5)*2),final_height

def fixed_resolution(preset_id,requested):
    profile=profile_for_id(preset_id)
    return f'{profile.height}p' if profile.height else requested


RATE_MODES = {'automatic': 'Automatic compression', 'quality': 'Constant quality'}
AUDIO_BITRATES = (128, 192, 256, 320)
AUDIO_CHANNELS = ('Original channels', 'Stereo', 'Mono')


def automatic_video_bitrate(preset_id, info):
    """Shutter-equivalent pixel/fps budget, independently expressed in kb/s.

    The existing RFM encoder outputs 8-bit pixels. Probe dimensions already
    account for rotation; fixed-height outputs also normalise sample aspect.
    This is a bitrate target, not a promise about final size or visual quality.
    """
    profile = profile_for_id(preset_id)
    if profile.family is None:
        return None
    width, height, fps = info['width'], info['height'], info['fps']
    if min(width, height, fps) <= 0 or not all(math.isfinite(x) for x in (width, height, fps)):
        raise ValueError('Cannot calculate automatic bitrate: source dimensions or frame rate are unknown. Choose Constant quality instead.')
    if profile.height:
        width, height = output_dimensions(width, height, profile.height, sar=info.get('sar', (1, 1)))
    divisor = {'h264': 165888, 'hevc': 331776, 'av1': 414720}[profile.family]
    # Positive half-up rounding, with a minimum usable rate for tiny media.
    return max(1, math.floor(width * height * fps * 8 * 2 / divisor + .5))


def video_compression_arguments(arguments, family, engine, rate_mode, bitrate,
                                max_quality, audio_bitrate, audio_channels,
                                *, compatibility=False):
    """Apply one-pass compression/audio choices without changing stream mapping."""
    values = list(arguments)
    if family is None:
        return values
    if rate_mode not in RATE_MODES or audio_bitrate not in AUDIO_BITRATES or audio_channels not in AUDIO_CHANNELS:
        raise ValueError('Unknown video compression or audio choice')
    def remove(*options):
        for option in options:
            while option in values:
                at = values.index(option)
                del values[at:at + 2]
    def set_option(option, value):
        remove(option)
        values.extend((option, str(value)))
    if rate_mode == 'automatic':
        if not isinstance(bitrate, int) or bitrate <= 0:
            raise ValueError('Automatic compression requires a valid calculated video bitrate')
        remove('-crf', '-cq', '-qp', '-qp_i', '-qp_p', '-qp_b', '-global_quality')
        set_option('-b:v', f'{bitrate}k')
        if engine == 'NVIDIA NVENC':
            set_option('-rc', 'vbr')
        elif engine == 'AMD AMF':
            set_option('-rc', 'vbr_peak')
    set_option('-b:a', f'{audio_bitrate}k')
    if audio_channels != 'Original channels':
        set_option('-ac', 2 if audio_channels == 'Stereo' else 1)
    if max_quality:
        if engine == 'NVIDIA NVENC':
            set_option('-preset', 'p7')
            if not compatibility:
                set_option('-tune', 'hq')
                set_option('-rc-lookahead', 32)
                set_option('-spatial-aq', 1)
                set_option('-aq-strength', 8)
        elif engine == 'Software / CPU':
            set_option('-preset', '0' if family == 'av1' else 'veryslow')
        elif engine == 'Intel Quick Sync':
            set_option('-preset', 'veryslow')
        # AMF already uses its quality preset; VAAPI retains driver defaults.
    return values
