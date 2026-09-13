import React from 'react';
import {Frame,Title,Small,Card} from '../Design';
export const PromiseScene:React.FC=()=> <Frame label="Local-first prototype"><Title>Keep the first decision.<br/>Make the retry quiet.</Title><div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:28,marginTop:55}}><Card hot>First delivery<br/><b>One saved decision</b></Card><Card>Same event again<br/><b>No repeated action</b></Card></div><Small>Fictional events. No live inbox. No notifications sent.</Small></Frame>;
