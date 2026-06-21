import * as vscode from 'vscode';
import { HivePulseClient } from '../HivePulseClient';

export class StargatePanel {
    private static currentPanel: StargatePanel | undefined;
    private _panel: vscode.WebviewPanel;
    private _disposables: vscode.Disposable[] = [];

    private constructor(panel: vscode.WebviewPanel, hiveClient: HivePulseClient) {
        this._panel = panel;
        this._panel.webview.html = this.getHtml();
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage(msg => {
            if (msg.command === 'scrub') hiveClient.requestSlice(msg.redshift);
        });
    }

    public static create(extensionUri: vscode.Uri, hiveClient: HivePulseClient): StargatePanel {
        const panel = vscode.window.createWebviewPanel('stargateView', 'Stargate View', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
        return new StargatePanel(panel, hiveClient);
    }

    public reveal() { this._panel.reveal(); }
    public scrubToRedshift(z: number) { this._panel.webview.postMessage({ command: 'scrubTo', redshift: z }); }
    public toggleLayer(id: string) { this._panel.webview.postMessage({ command: 'toggleLayer', layerId: id }); }
    public toggleGold() { this._panel.webview.postMessage({ command: 'toggleGold' }); }
    public exportSlice(fmt: string) { this._panel.webview.postMessage({ command: 'export', format: fmt }); }
    public onDidDispose(cb: () => void) { this._panel.onDidDispose(cb); }

    private getHtml(): string {
        return `<!DOCTYPE html><html><head><style>
            body{background:#0a0a0f;color:#e0e0e0;font-family:system-ui,sans-serif;display:flex;flex-direction:column;height:100vh;margin:0}
            #header{background:linear-gradient(90deg,#1a1a2e,#16213e);padding:12px 20px;display:flex;justify-content:space-between;align-items:center}
            #title{font-size:16px;font-weight:600;color:#ffd700}
            #canvas{flex:1;width:100%}
            #controls{background:linear-gradient(0deg,rgba(0,0,0,.9),transparent);padding:16px 20px}
            #slider{width:100%;height:6px;-webkit-appearance:none;background:linear-gradient(90deg,#ffd700,#ff6b00,#00ff88);border-radius:3px;outline:0}
            #slider::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;background:#ffd700;border-radius:50%;cursor:pointer}
            .btns{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}
            .btn{padding:4px 10px;border-radius:12px;border:1px solid #333;background:rgba(255,255,255,.05);color:#888;font-size:11px;cursor:pointer}
            .btn.active{background:rgba(255,215,0,.2);border-color:#ffd700;color:#ffd700}
            #gold-btn{position:absolute;top:50%;right:20px;transform:translateY(-50%);padding:8px 16px;border-radius:20px;border:2px solid #ffd700;background:rgba(255,215,0,.1);color:#ffd700;cursor:pointer}
            #stats{position:absolute;top:50px;right:20px;background:rgba(0,0,0,.6);border-radius:8px;padding:12px;font-size:11px}
            .row{display:flex;justify-content:space-between;gap:20px;margin-bottom:4px}
            .lbl{color:#666}.val{color:#ccc}
        </style></head><body>
        <div id="header"><div id="title">THE UNIVERSAL MAP</div><div id="hive-status" style="font-size:11px;color:#666">Hive: Connecting...</div></div>
        <canvas id="canvas"></canvas>
        <button id="gold-btn" class="active">RAIN OF GOLD</button>
        <div id="stats"><div class="row"><span class="lbl">z</span><span class="val" id="sz">0</span></div><div class="row"><span class="lbl">Lookback</span><span class="val" id="sl">0 Gyr</span></div><div class="row"><span class="lbl">Age</span><span class="val" id="sa">13.8 Gyr</span></div></div>
        <div id="controls">
            <input type="range" id="slider" min="0" max="1100" value="0" step="0.1">
            <div class="btns">
                <button class="btn" data-l="l0_cmb">CMB</button>
                <button class="btn" data-l="l1_dark_matter">DM</button>
                <button class="btn" data-l="l2_filaments">Filaments</button>
                <button class="btn" data-l="l3_nodes">Nodes</button>
                <button class="btn active" data-l="l4_galaxies">Galaxies</button>
                <button class="btn" data-l="l5_reionization">Reion</button>
                <button class="btn" data-l="l6_21cm">21cm</button>
                <button class="btn active" data-l="l_gold">Gold</button>
            </div>
        </div>
        <script>
            const vscode=acquireVsCodeApi();
            const c=document.getElementById('canvas'),ctx=c.getContext('2d');
            let t=0,z=0,gold=true,layers=['l4_galaxies','l_gold'];
            function resize(){c.width=window.innerWidth;c.height=window.innerHeight}
            window.addEventListener('resize',resize);resize();
            function render(){
                t+=.01;ctx.fillStyle='#0a0a0f';ctx.fillRect(0,0,c.width,c.height);
                const cx=c.width/2,cy=c.height/2,R=Math.min(cx,cy)*.5,r=R*.3;
                // Torus
                ctx.strokeStyle='rgba(100,100,150,.15)';ctx.lineWidth=1;
                for(let i=0;i<60;i++){const p=i/60*Math.PI*2;ctx.beginPath();
                    for(let j=0;j<=20;j++){const th=j/20*Math.PI*2;
                        const x=cx+(R+r*Math.cos(th))*Math.cos(p),y=cy+r*Math.sin(th)*.5;
                        j===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
                    }ctx.stroke();
                }
                // Galaxies
                if(layers.includes('l4_galaxies')){ctx.fillStyle='rgba(150,180,255,.4)';
                    for(let i=0;i<200;i++){const p=i/200*Math.PI*2+t*.1,th=Math.sin(i*.1+t*.5)*Math.PI;
                        ctx.beginPath();ctx.arc(cx+(R+r*Math.cos(th))*Math.cos(p),cy+r*Math.sin(th)*.5,1.5,0,Math.PI*2);ctx.fill();
                    }
                }
                // Gold
                if(gold){for(let i=0;i<50;i++){
                    const x=(Math.sin(i*1.7+t)*.5+.5)*c.width,y=(t*50+i*20)%c.height;
                    const g=ctx.createRadialGradient(x,y,0,x,y,4);
                    g.addColorStop(0,'rgba(255,215,0,.8)');g.addColorStop(1,'rgba(255,150,0,0)');
                    ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,4,0,Math.PI*2);ctx.fill();
                }}
                // Timeline bar
                const bw=c.width*.6,bx=(c.width-bw)/2,by=c.height-80;
                ctx.fillStyle='rgba(255,255,255,.05)';ctx.fillRect(bx,by,bw,4);
                const grad=ctx.createLinearGradient(bx,0,bx+bw,0);
                grad.addColorStop(0,'#ffd700');grad.addColorStop(.5,'#ff6b00');grad.addColorStop(1,'#00ff88');
                ctx.fillStyle=grad;ctx.fillRect(bx,by,bw*(z/1100),4);
                requestAnimationFrame(render);
            }
            render();
            document.getElementById('slider').addEventListener('input',e=>{
                z=parseFloat(e.target.value);
                document.getElementById('sz').textContent=z.toFixed(1);
                document.getElementById('sl').textContent=(z<1?z*.01:z*.8).toFixed(2)+' Gyr';
                document.getElementById('sa').textContent=(13.8-(z<1?z*.01:z*.8)).toFixed(1)+' Gyr';
                vscode.postMessage({command:'scrub',redshift:z});
            });
            document.querySelectorAll('.btn').forEach(b=>{
                b.addEventListener('click',()=>{b.classList.toggle('active');vscode.postMessage({command:'toggleLayer',layerId:b.dataset.l});});
            });
            document.getElementById('gold-btn').addEventListener('click',()=>{
                gold=!gold;document.getElementById('gold-btn').classList.toggle('active');vscode.postMessage({command:'toggleGold'});
            });
            window.addEventListener('message',e=>{
                const m=e.data;
                if(m.command==='scrubTo'){z=m.redshift;document.getElementById('slider').value=z;}
            });
        </script></body></html>`;
    }

    public dispose() {
        StargatePanel.currentPanel = undefined;
        this._panel.dispose();
        this._disposables.forEach(d => d.dispose());
    }
}
