import * as vscode from 'vscode';

export class LayerTreeProvider implements vscode.TreeDataProvider<LayerItem> {
    private layers = [
        { id: 'l0_cmb', label: 'CMB', desc: 'Cosmic Microwave Background' },
        { id: 'l1_dark_matter', label: 'Dark Matter', desc: 'Dark Matter Distribution' },
        { id: 'l2_filaments', label: 'Filaments', desc: 'Cosmic Filaments' },
        { id: 'l3_nodes', label: 'Nodes', desc: 'Cluster Nodes' },
        { id: 'l4_galaxies', label: 'Galaxies', desc: 'Galaxy Distribution' },
        { id: 'l5_reionization', label: 'Reionization', desc: 'Reionization History' },
        { id: 'l6_21cm', label: '21cm', desc: '21cm Signal' },
        { id: 'l_gold', label: 'Rain of Gold', desc: 'Negentropic Overlay' },
    ];

    getTreeItem(element: LayerItem): vscode.TreeItem { return element; }
    getChildren(): Thenable<LayerItem[]> {
        return Promise.resolve(this.layers.map(l => new LayerItem(l.id, l.label, l.desc)));
    }
}

class LayerItem extends vscode.TreeItem {
    constructor(public readonly id: string, label: string, desc: string) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.tooltip = desc;
        this.command = { command: 'stargate-view.toggleLayer', title: 'Toggle', arguments: [this.id] };
    }
}
