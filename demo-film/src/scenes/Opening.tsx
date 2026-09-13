import React from 'react';
import {interpolate,useCurrentFrame} from 'remotion';
import {Frame,Title,Small,coral,mint,ink} from '../Design';
export const Opening:React.FC=()=>{const f=useCurrentFrame();return <Frame label="The problem · editorial illustration">
 <div style={{display:'flex',gap:80,alignItems:'center'}}><div style={{width:'57%'}}><Title>Not every update<br/>deserves a bell.</Title><Small>For independent makers juggling<br/>contest messages and deadlines.</Small></div>
 <div style={{position:'relative',width:570,height:480}}>
 {[0,1,2].map(i=><div key={i} style={{position:'absolute',background:mint,border:'2px solid #aec3b5',width:340,height:95,borderRadius:12,left:i*15,top:240+i*35,rotate:`${i*3-5}deg`,boxShadow:'0 12px 0 #c9d9c9'}}/>)}
 <div style={{position:'absolute',top:55,left:200,width:170,height:200,borderRadius:'90px 90px 18px 18px',background:coral,rotate:`${interpolate(f,[0,18,30,42,70],[-6,5,-3,2,0],{extrapolateRight:'clamp'})}deg`,boxShadow:'10px 14px 0 #d8735e'}}><div style={{position:'absolute',width:58,height:35,borderRadius:'0 0 40px 40px',background:ink,bottom:-22,left:57}}/></div>
 </div></div></Frame>};
