import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
export const ink='#17392f', paper='#f7f3e9', mint='#d7eade', coral='#e5856f', muted='#526e62';
export const Frame: React.FC<{children:React.ReactNode; label:string}> = ({children,label}) => {
 const f=useCurrentFrame();
 return <AbsoluteFill style={{background:paper,color:ink,fontFamily:'Arial, sans-serif',padding:'110px 125px 220px'}}>
  <div style={{fontSize:24,letterSpacing:4,textTransform:'uppercase',color:muted,marginBottom:35}}>Only When It Matters <span style={{float:'right',fontSize:22,letterSpacing:1}}>{label}</span></div>
  <div style={{opacity:interpolate(f,[0,10],[0,1],{extrapolateRight:'clamp'})}}>{children}</div>
 </AbsoluteFill>;
};
export const Title:React.FC<{children:React.ReactNode}> = ({children}) => <h1 style={{fontFamily:'Georgia, serif',fontSize:86,fontWeight:400,letterSpacing:-3,lineHeight:1.07,margin:'10px 0 35px'}}>{children}</h1>;
export const Small:React.FC<{children:React.ReactNode}> = ({children})=><p style={{fontSize:32,lineHeight:1.45,color:muted,margin:'18px 0'}}>{children}</p>;
export const Card:React.FC<{children:React.ReactNode;hot?:boolean}> = ({children,hot})=><div style={{padding:28,borderRadius:18,background:hot?'#f4d4c5':mint,border:'1px solid #bfcfc2',fontSize:32,lineHeight:1.4}}>{children}</div>;
