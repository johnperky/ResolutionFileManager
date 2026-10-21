// Load from the Computer Use node session. One input per call, then inspect
// the returned native screenshot before requesting another input. No blind loop.
import {sky} from '@oai/sky';
import fs from 'node:fs/promises';
import path from 'node:path';

export async function createCaptureSession(root, version='12.7.4') {
  await fs.mkdir(root,{recursive:true});
  const manifest=path.join(root,'capture-progress.json');
  let records=[];
  try { records=JSON.parse(await fs.readFile(manifest,'utf8')); }
  catch(error) { if(error.code!=='ENOENT') throw error; }
  let window,state;
  async function observe() {
    state=await sky.get_window_state({window});
    window=state.window;
    return state;
  }
  async function select() {
    const candidates=(await sky.list_windows()).filter(w=>w.app.toLowerCase().endsWith(`resolutionfilemanager-v${version}-multilingual-review.exe`) && w.title?.endsWith(version));
    if(candidates.length!==1) throw Error(`Expected one review window, found ${candidates.length}`);
    window=await sky.get_window({id:candidates[0].id,app:candidates[0].app});
    await sky.activate_window({window});
    return observe();
  }
  async function act(method,args) {
    if(!state) throw Error('Observe the current window before acting');
    if(!['click','press_key','type_text','drag','scroll'].includes(method)) throw Error('Unsupported input');
    const current=window;state=null;
    await sky[method]({...args,window:current});
    return observe();
  }
  async function save(language,name,{reviewed=false}={}) {
    if(!reviewed) throw Error('Visually review the native capture before saving');
    if(!state) throw Error('No current native capture');
    const shot=state.screenshots[0];
    if(shot.width!==1920||shot.height!==1032) throw Error('Expected maximized 1920 × 1032 taskbar-free window');
    if(!['01-details-info','02-dual-previews','03-thumbnails','04-video-conversion'].includes(name)) throw Error('Unknown layout');
    const match=shot.url.match(/^data:(image\/(?:png|jpeg));base64,(.*)$/s);
    if(!match) throw Error('Unexpected native capture format');
    const destination=path.join(root,language,`${name}.${match[1]==='image/png'?'png':'jpg'}`);
    await fs.mkdir(path.dirname(destination),{recursive:true});
    // Preserve any earlier capture rather than overwrite its only copy.
    try {await fs.access(destination);throw Error(`Capture already exists: ${destination}`);}
    catch(error){if(error.code!=='ENOENT')throw error;}
    await fs.writeFile(destination,Buffer.from(match[2],'base64'));
    records.push({language,name,path:destination,width:shot.width,height:shot.height,mime:match[1],reviewed:true});
    await fs.writeFile(manifest,JSON.stringify(records,null,2)+'\n');
    return destination;
  }
  return {select,observe,act,save,progress:()=>records};
}
