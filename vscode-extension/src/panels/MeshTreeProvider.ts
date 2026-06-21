import * as vscode from 'vscode';
import { MeshSyncClient } from '../MeshSyncClient';

export class MeshTreeProvider implements vscode.TreeDataProvider<MeshItem> {
    private client: MeshSyncClient | undefined;

    constructor(client?: MeshSyncClient) { this.client = client; }

    getTreeItem(element: MeshItem): vscode.TreeItem { return element; }
    getChildren(): Thenable<MeshItem[]> {
        const peers = this.client?.getPeers() || [];
        if (peers.length === 0) {
            return Promise.resolve([new MeshItem('no-peers', 'No mesh peers connected', '')]);
        }
        return Promise.resolve(peers.map(p => new MeshItem(p, p, 'peer')));
    }
}

class MeshItem extends vscode.TreeItem {
    constructor(public readonly id: string, label: string, type: string) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.iconPath = new vscode.ThemeIcon(type === 'peer' ? 'radio-tower' : 'info');
    }
}
