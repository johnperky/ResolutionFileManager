"""Conventional streaming filters; no neural model or frame-file staging."""


def effective_video_mode(mode, source_height, target_height):
    if not target_height:return 'ordinary'
    return mode if mode=='fast_video' or source_height<target_height else 'ordinary'


def fast_video_arguments(arguments, engine):
    values=list(arguments)
    chain=''
    if '-vf' in values:
        at=values.index('-vf');chain=values[at+1];del values[at:at+2]
    filters=chain.split(',') if chain else []
    for i,value in enumerate(filters):
        if value.startswith('scale=') and 'flags=' not in value:
            filters[i]=value+':flags=lanczos'
    # VA-API software-decode frames must be filtered before uploading.
    at=next((i for i,value in enumerate(filters) if value.startswith('format=') or value=='hwupload'),len(filters))
    filters.insert(at,'unsharp=3:3:0.3:3:3:0')
    values+=['-vf',','.join(filters),'-fps_mode','passthrough','-enc_time_base','1:1000000']
    return values


def preserve_streams(arguments, extension, source_index=0):
    """Map every audio/subtitle stream; unsupported codecs must fail visibly."""
    values=list(arguments)
    if '-map_chapters' not in values:values+=['-map_chapters',str(source_index)]
    values+=['-map',f'{source_index}:s?','-c:s','mov_text' if extension.lower()=='.mp4' else 'copy']
    return values


VIDEO_EFFECTS=('Denoise','Sharpen','Smooth','Contrast boost','Colour boost')


def video_effect_arguments(arguments,effects=(),strength=2):
    """Software filters work with CPU and hardware encoders, before upload."""
    values=list(arguments);selected=set(effects)
    if selected-set(VIDEO_EFFECTS):raise ValueError('Unknown video effect')
    if strength not in (1,2,3):raise ValueError('Unknown video effect strength')
    if not selected:return values
    chain=[]
    if '-vf' in values:
        at=values.index('-vf');chain=values[at+1].split(',');del values[at:at+2]
    # Replace Fast's existing light sharpening only when explicitly overridden.
    if 'Sharpen' in selected:chain=[f for f in chain if not f.startswith('unsharp=')]
    filters=[]
    if 'Denoise' in selected:filters.append(f'hqdn3d={1.5*strength:g}:{strength:g}:{2*strength:g}:{1.5*strength:g}')
    if 'Smooth' in selected:filters.append(f'gblur=sigma={.3*strength:g}')
    equalizer=[]
    if 'Contrast boost' in selected:equalizer.append(f'contrast={1+.04*strength:g}')
    if 'Colour boost' in selected:equalizer.append(f'saturation={1+.1*strength:g}')
    if equalizer:filters.append('eq='+':'.join(equalizer))
    if 'Sharpen' in selected:filters.append(f'unsharp=5:5:{.25*strength:g}:5:5:0')
    at=next((i for i,f in enumerate(chain) if f.startswith('format=') or f=='hwupload'),len(chain))
    chain[at:at]=filters
    return values+['-vf',','.join(chain)]
