import * as vscode from 'vscode';

export class TimelineTreeProvider implements vscode.TreeDataProvider<TimelineItem> {
    private slices = [
        { id: 'z1100', name: 'Surface of Last Scattering', z: 1100 },
        { id: 'z20_10', name: 'Cosmic Dawn', z: '20-10' },
        { id: 'z10_6', name: 'Reionization', z: '10-6' },
        { id: 'z6_3', name: 'Galaxy Assembly', z: '6-3' },
        { id: 'z3_1', name: 'Web Maturation', z: '3-1' },
        { id: 'z1_0.5', name: 'Web Refinement', z: '1-0.5' },
        { id: 'z0.5_0', name: 'Present Expansion', z: '0.5-0' },
    ];

    getTreeItem(element: TimelineItem): vscode.TreeItem { return element; }
    getChildren(): Thenable<TimelineItem[]> {
        return Promise.resolve(this.slices.map(s => new TimelineItem(s.id, s.name, s.z)));
    }
}

class TimelineItem extends vscode.TreeItem {
    constructor(public readonly id: string, name: string, z: string | number) {
        super(name, vscode.TreeItemCollapsibleState.None);
        this.description = 'z=' + z;
        this.iconPath = new vscode.ThemeIcon('clock');
    }
}
