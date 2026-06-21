import * as vscode from 'vscode';
import { StargatePanel } from './panels/StargatePanel';
import { LayerTreeProvider } from './panels/LayerTreeProvider';
import { TimelineTreeProvider } from './panels/TimelineTreeProvider';
import { MeshTreeProvider } from './panels/MeshTreeProvider';
import { HivePulseClient } from './HivePulseClient';
import { MeshSyncClient } from './MeshSyncClient';

let stargatePanel: StargatePanel | undefined;
let hiveClient: HivePulseClient | undefined;
let meshClient: MeshSyncClient | undefined;

export function activate(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('stargate-view');
    const api = config.get<string>('apiEndpoint', 'http://localhost:8080');
    const ws = config.get<string>('wsEndpoint', 'ws://localhost:8080/map/ws');
    const mesh = config.get<boolean>('meshEnabled', true);

    hiveClient = new HivePulseClient(api, ws);
    if (mesh) meshClient = new MeshSyncClient();

    vscode.window.registerTreeDataProvider('stargate-view.layers', new LayerTreeProvider());
    vscode.window.registerTreeDataProvider('stargate-view.timeline', new TimelineTreeProvider());
    vscode.window.registerTreeDataProvider('stargate-view.mesh', new MeshTreeProvider(meshClient));

    context.subscriptions.push(
        vscode.commands.registerCommand('stargate-view.open', () => {
            if (stargatePanel) stargatePanel.reveal();
            else {
                stargatePanel = StargatePanel.create(context.extensionUri, hiveClient!);
                stargatePanel.onDidDispose(() => { stargatePanel = undefined; });
            }
        }),
        vscode.commands.registerCommand('stargate-view.scrubTime', async () => {
            const z = await vscode.window.showInputBox({ prompt: 'Redshift (0-1100)' });
            if (z) stargatePanel?.scrubToRedshift(parseFloat(z));
        }),
        vscode.commands.registerCommand('stargate-view.toggleLayer', async () => {
            const layers = ['l0_cmb','l1_dark_matter','l2_filaments','l3_nodes','l4_galaxies','l5_reionization','l6_21cm','l_gold'];
            const pick = await vscode.window.showQuickPick(layers);
            if (pick) stargatePanel?.toggleLayer(pick);
        }),
        vscode.commands.registerCommand('stargate-view.toggleGold', () => stargatePanel?.toggleGold()),
        vscode.commands.registerCommand('stargate-view.syncMesh', async () => {
            if (meshClient) await meshClient.sync();
        }),
        vscode.commands.registerCommand('stargate-view.exportSlice', async () => {
            const fmt = await vscode.window.showQuickPick(['GeoJSON','CSV','JSON','FITS']);
            if (fmt) stargatePanel?.exportSlice(fmt.toLowerCase());
        }),
        vscode.commands.registerCommand('stargate-view.pulseStatus', () => {
            const s = hiveClient?.getStatus();
            vscode.window.showInformationMessage('Hive: ' + (s?.connected ? 'Connected' : 'Disconnected'));
        })
    );

    vscode.commands.executeCommand('setContext', 'stargate-view.active', true);
    console.log('Stargate View activated');
}

export function deactivate() {
    hiveClient?.disconnect();
    meshClient?.disconnect();
}
