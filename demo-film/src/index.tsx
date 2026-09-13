import React from 'react';
import {AbsoluteFill,Composition,registerRoot,staticFile,useCurrentFrame} from 'remotion';
import {Audio} from '@remotion/media';
import {TransitionSeries} from '@remotion/transitions';
import {Opening} from './scenes/Opening';
import {PromiseScene} from './scenes/Promise';
import {Replay} from './scenes/Replay';
import {ModelProof} from './scenes/ModelProof';
import {Guard} from './scenes/Guard';
import {Close} from './scenes/Close';
import captions from './captions.json';
const Film:React.FC=()=>{const t=useCurrentFrame()/30; const caption=captions.find(c=>t>=c.start&&t<c.end);return <AbsoluteFill>
 <TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={396}><Opening/></TransitionSeries.Sequence>
  <TransitionSeries.Sequence durationInFrames={378}><PromiseScene/></TransitionSeries.Sequence>
  <TransitionSeries.Sequence durationInFrames={561}><Replay/></TransitionSeries.Sequence>
  <TransitionSeries.Sequence durationInFrames={669}><ModelProof/></TransitionSeries.Sequence>
  <TransitionSeries.Sequence durationInFrames={492}><Guard/></TransitionSeries.Sequence>
  <TransitionSeries.Sequence durationInFrames={804}><Close/></TransitionSeries.Sequence>
 </TransitionSeries>
 <Audio src={staticFile('narration.mp3')}/>
 <div style={{position:'absolute',left:125,right:125,bottom:74,minHeight:92,display:'flex',alignItems:'center',justifyContent:'center',background:'#17392f',color:'#fffaf0',padding:'12px 45px',borderRadius:12,fontFamily:'Arial, sans-serif',fontSize:31,lineHeight:1.35,textAlign:'center'}}>{caption?.text??''}</div>
 <div style={{position:'absolute',bottom:27,left:125,fontSize:21,color:'#526e62',fontFamily:'Arial, sans-serif'}}>Voiceover Generated with AIDOCMAKER.COM · Fictional demo data · No submission claim</div>
 </AbsoluteFill>};
const Root:React.FC=()=> <Composition id="OnlyWhenItMatters" component={Film} durationInFrames={3300} fps={30} width={1920} height={1080}/>;
registerRoot(Root);
