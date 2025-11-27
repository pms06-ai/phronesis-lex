// Entity Map Component - Relationship Visualization
// Uses real extracted data from investigation-engine
function registerEntityMap() {
    Alpine.data('entityMapComponent', () => ({
        filterType: 'all',
        filterDocument: 'all',
        searchQuery: '',
        selectedNode: null,
        network: null,
        nodes: null,
        edges: null,
        allNodes: [],
        allEdges: [],
        layoutType: 'mindmap',
        highlightedNodes: new Set(),
        minStrength: 2,

        // Entity type configuration
        entityTypeConfig: {
            'UK_JUDGE': {
                color: { background: '#C9AE5D', border: '#B5A642', highlight: { background: '#D4C36A', border: '#C9AE5D' } },
                icon: 'gavel',
                label: 'Judge',
                level: 0
            },
            'UK_LOCAL_AUTHORITY': {
                color: { background: '#8B7B3A', border: '#6B5B2A', highlight: { background: '#9C8C4B', border: '#8B7B3A' } },
                icon: 'account_balance',
                label: 'Authority',
                level: 1
            },
            'UK_POLICE_FORCE': {
                color: { background: '#6B7280', border: '#4B5563', highlight: { background: '#9CA3AF', border: '#6B7280' } },
                icon: 'local_police',
                label: 'Police',
                level: 1
            },
            'UK_COURT': {
                color: { background: '#D4C36A', border: '#C9AE5D', highlight: { background: '#E4D37A', border: '#D4C36A' } },
                icon: 'balance',
                label: 'Court',
                level: 0
            },
            'CASE_NUMBER': {
                color: { background: '#9CA3AF', border: '#6B7280', highlight: { background: '#D1D5DB', border: '#9CA3AF' } },
                icon: 'folder',
                label: 'Case',
                level: 2
            },
            'SOLICITOR_FIRM': {
                color: { background: '#B5A642', border: '#8B7B3A', highlight: { background: '#C9AE5D', border: '#B5A642' } },
                icon: 'work',
                label: 'Legal',
                level: 1
            },
            'DATE': {
                color: { background: '#454d57', border: '#363c44', highlight: { background: '#5a6370', border: '#454d57' } },
                icon: 'calendar_today',
                label: 'Date',
                level: 2
            }
        },

        initNetwork() {
            const container = document.getElementById('entity-network');
            if (!container) return;

            this.buildNetworkData();
            this.renderNetwork(container);
        },

        buildNetworkData() {
            this.allNodes = [];
            this.allEdges = [];

            const store = Alpine.store('case');

            // Use unique entities from real data (exclude dates for cleaner visualization)
            const entities = store.uniqueEntities.filter(e => e.type !== 'DATE');

            // Build nodes from unique entities
            entities.forEach((entity, idx) => {
                const config = this.entityTypeConfig[entity.type] || this.entityTypeConfig['CASE_NUMBER'];
                const size = Math.min(35, Math.max(15, 10 + entity.occurrences * 0.5));

                this.allNodes.push({
                    id: entity.id,
                    label: entity.name,
                    title: this.buildTooltip(entity),
                    type: entity.type,
                    occurrences: entity.occurrences,
                    documents: entity.documents || [],
                    avgConfidence: entity.avgConfidence,
                    level: config.level,
                    color: config.color,
                    font: {
                        color: '#ffffff',
                        size: 11,
                        face: 'Source Sans 3',
                        strokeWidth: 4,
                        strokeColor: '#121416'
                    },
                    size: size,
                    borderWidth: 2,
                    shape: 'dot'
                });
            });

            // Build edges from relationships
            const relationships = store.relationships || [];

            relationships.forEach(rel => {
                if (rel.strength < this.minStrength) return;

                const fromNode = this.allNodes.find(n => n.id === rel.from);
                const toNode = this.allNodes.find(n => n.id === rel.to);

                if (!fromNode || !toNode) return;

                const edgeWidth = Math.min(5, Math.max(1, rel.strength * 0.3));
                const hasLabel = rel.label && rel.label !== null;

                this.allEdges.push({
                    from: rel.from,
                    to: rel.to,
                    label: hasLabel ? rel.label : '',
                    title: `${rel.fromName} ↔ ${rel.toName}\nCo-occurs in ${rel.strength} documents`,
                    relationshipType: rel.type || 'co-occurrence',
                    strength: rel.strength,
                    documents: rel.documents || [],
                    arrows: hasLabel ? { to: { enabled: true, scaleFactor: 0.5 } } : { to: { enabled: false } },
                    color: {
                        color: hasLabel ? this.getRelationshipEdgeColor(rel.type) : '#454d57',
                        highlight: '#C9AE5D',
                        opacity: 0.7
                    },
                    font: {
                        color: '#9CA3AF',
                        size: 9,
                        face: 'JetBrains Mono',
                        strokeWidth: 3,
                        strokeColor: '#121416',
                        background: '#1a1d21'
                    },
                    smooth: {
                        enabled: true,
                        type: 'curvedCW',
                        roundness: 0.2
                    },
                    width: edgeWidth,
                    hoverWidth: edgeWidth + 1
                });
            });
        },

        getRelationshipEdgeColor(type) {
            const colors = {
                'professional': '#3B82F6',
                'legal': '#22C55E',
                'institutional': '#F59E0B',
                'administrative': '#9CA3AF',
                'co-occurrence': '#454d57'
            };
            return colors[type] || colors['co-occurrence'];
        },

        buildTooltip(entity) {
            const config = this.entityTypeConfig[entity.type] || {};
            return `<div style="padding:10px;font-family:Source Sans 3;background:#22262b;border:1px solid #454d57;border-radius:8px;min-width:180px;">
                <strong style="color:#C9AE5D;font-size:14px;">${entity.name}</strong><br/>
                <span style="color:#9CA3AF;font-size:11px;">${config.label || entity.type}</span><br/>
                <hr style="border:none;border-top:1px solid #363c44;margin:6px 0;"/>
                <span style="color:#6B7280;font-size:10px;">Occurrences: ${entity.occurrences}</span><br/>
                <span style="color:#6B7280;font-size:10px;">Documents: ${entity.documents?.length || 0}</span><br/>
                <span style="color:#6B7280;font-size:10px;">Confidence: ${(entity.avgConfidence * 100).toFixed(0)}%</span>
            </div>`;
        },

        renderNetwork(container) {
            // Apply filters
            let filteredNodes = [...this.allNodes];
            let filteredEdges = [...this.allEdges];

            // Filter by entity type
            if (this.filterType !== 'all') {
                filteredNodes = this.allNodes.filter(n => n.type === this.filterType);
                const nodeIds = new Set(filteredNodes.map(n => n.id));
                filteredEdges = this.allEdges.filter(e => nodeIds.has(e.from) && nodeIds.has(e.to));
            }

            // Filter by document
            if (this.filterDocument !== 'all') {
                const docId = parseInt(this.filterDocument);
                filteredNodes = filteredNodes.filter(n => n.documents.includes(docId));
                const nodeIds = new Set(filteredNodes.map(n => n.id));
                filteredEdges = filteredEdges.filter(e =>
                    nodeIds.has(e.from) && nodeIds.has(e.to) && e.documents.includes(docId)
                );
            }

            // Apply search highlighting
            if (this.searchQuery.trim()) {
                const query = this.searchQuery.toLowerCase();
                this.highlightedNodes = new Set(
                    filteredNodes.filter(n => n.label.toLowerCase().includes(query)).map(n => n.id)
                );
                filteredNodes = filteredNodes.map(n => ({
                    ...n,
                    opacity: this.highlightedNodes.has(n.id) ? 1 : 0.25,
                    borderWidth: this.highlightedNodes.has(n.id) ? 4 : n.borderWidth
                }));
                filteredEdges = filteredEdges.map(e => ({
                    ...e,
                    hidden: !this.highlightedNodes.has(e.from) && !this.highlightedNodes.has(e.to)
                }));
            } else {
                this.highlightedNodes.clear();
            }

            this.nodes = new vis.DataSet(filteredNodes);
            this.edges = new vis.DataSet(filteredEdges);

            const data = { nodes: this.nodes, edges: this.edges };
            const options = this.getNetworkOptions();

            if (this.network) {
                this.network.destroy();
            }
            this.network = new vis.Network(container, data, options);

            // Click handler
            this.network.on('click', (params) => {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const node = this.nodes.get(nodeId);
                    const connections = this.getConnectedEntities(nodeId);
                    this.selectedNode = { ...node, connections };
                } else {
                    this.selectedNode = null;
                }
            });

            // Double-click to focus
            this.network.on('doubleClick', (params) => {
                if (params.nodes.length > 0) {
                    this.network.focus(params.nodes[0], {
                        scale: 1.2,
                        animation: { duration: 400, easingFunction: 'easeInOutQuad' }
                    });
                }
            });

            // Fit after stabilization
            this.network.once('stabilized', () => {
                this.network.fit({
                    animation: { duration: 500, easingFunction: 'easeInOutQuad' },
                    padding: 50
                });
            });
        },

        getNetworkOptions() {
            const baseOptions = {
                nodes: {
                    shape: 'dot',
                    shadow: {
                        enabled: true,
                        color: 'rgba(0,0,0,0.4)',
                        x: 3,
                        y: 3,
                        size: 8
                    }
                },
                edges: {
                    shadow: {
                        enabled: true,
                        color: 'rgba(0,0,0,0.2)',
                        x: 2,
                        y: 2,
                        size: 4
                    }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 150,
                    zoomView: true,
                    dragView: true,
                    keyboard: { enabled: true },
                    zoomSpeed: 0.8
                }
            };

            if (this.layoutType === 'mindmap') {
                return {
                    ...baseOptions,
                    layout: { improvedLayout: false },
                    physics: {
                        enabled: true,
                        stabilization: { enabled: true, iterations: 300, updateInterval: 10 },
                        solver: 'repulsion',
                        repulsion: {
                            centralGravity: 0.8,
                            springLength: 180,
                            springConstant: 0.05,
                            nodeDistance: 150,
                            damping: 0.5
                        }
                    },
                    edges: {
                        ...baseOptions.edges,
                        smooth: { enabled: true, type: 'cubicBezier', roundness: 0.5 }
                    }
                };
            }

            if (this.layoutType === 'hierarchical') {
                return {
                    ...baseOptions,
                    layout: {
                        hierarchical: {
                            enabled: true,
                            direction: 'UD',
                            sortMethod: 'directed',
                            levelSeparation: 120,
                            nodeSpacing: 180,
                            treeSpacing: 220,
                            blockShifting: true,
                            edgeMinimization: true,
                            parentCentralization: true
                        }
                    },
                    physics: { enabled: false },
                    edges: {
                        ...baseOptions.edges,
                        smooth: { enabled: true, type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 }
                    }
                };
            }

            // Physics/organic layout
            return {
                ...baseOptions,
                layout: { improvedLayout: true, randomSeed: 42 },
                physics: {
                    enabled: true,
                    stabilization: { enabled: true, iterations: 200, updateInterval: 25 },
                    barnesHut: {
                        gravitationalConstant: -3000,
                        centralGravity: 0.3,
                        springLength: 150,
                        springConstant: 0.05,
                        damping: 0.4,
                        avoidOverlap: 0.5
                    }
                },
                edges: {
                    ...baseOptions.edges,
                    smooth: { enabled: true, type: 'continuous', roundness: 0.5 }
                }
            };
        },

        getConnectedEntities(nodeId) {
            const connections = [];
            this.allEdges.forEach(edge => {
                if (edge.from === nodeId) {
                    const target = this.allNodes.find(n => n.id === edge.to);
                    if (target) connections.push({
                        node: target,
                        label: edge.label || 'co-occurrence',
                        type: edge.relationshipType,
                        strength: edge.strength,
                        direction: 'outgoing'
                    });
                } else if (edge.to === nodeId) {
                    const source = this.allNodes.find(n => n.id === edge.from);
                    if (source) connections.push({
                        node: source,
                        label: edge.label || 'co-occurrence',
                        type: edge.relationshipType,
                        strength: edge.strength,
                        direction: 'incoming'
                    });
                }
            });
            // Sort by strength
            return connections.sort((a, b) => b.strength - a.strength);
        },

        applyFilter() {
            const container = document.getElementById('entity-network');
            if (container) this.renderNetwork(container);
        },

        applySearch() {
            const container = document.getElementById('entity-network');
            if (container) this.renderNetwork(container);
        },

        clearSearch() {
            this.searchQuery = '';
            this.applySearch();
        },

        resetView() {
            if (this.network) {
                this.network.fit({
                    animation: { duration: 400, easingFunction: 'easeInOutQuad' },
                    padding: 50
                });
            }
        },

        zoomIn() {
            if (this.network) {
                const scale = this.network.getScale();
                this.network.moveTo({ scale: scale * 1.4, animation: { duration: 250 } });
            }
        },

        zoomOut() {
            if (this.network) {
                const scale = this.network.getScale();
                this.network.moveTo({ scale: scale / 1.4, animation: { duration: 250 } });
            }
        },

        setLayout(layout) {
            this.layoutType = layout;
            const container = document.getElementById('entity-network');
            if (container) this.renderNetwork(container);
        },

        getNodeColorClass(type) {
            const classes = {
                'UK_JUDGE': 'bg-accent-brass',
                'UK_LOCAL_AUTHORITY': 'bg-accent-bronze',
                'UK_POLICE_FORCE': 'bg-accent-steel',
                'UK_COURT': 'bg-accent-copper',
                'CASE_NUMBER': 'bg-accent-silver',
                'SOLICITOR_FIRM': 'bg-accent-gold',
                'DATE': 'bg-dark-500'
            };
            return classes[type] || 'bg-accent-brass';
        },

        getNodeIcon(type) {
            const config = this.entityTypeConfig[type];
            return config ? config.icon : 'circle';
        },

        getNodeTypeLabel(type) {
            const config = this.entityTypeConfig[type];
            return config ? config.label : type;
        },

        getConnectionCount(nodeId) {
            return this.allEdges.filter(e => e.from === nodeId || e.to === nodeId).length;
        },

        // Get available documents for filter dropdown
        get availableDocuments() {
            return Alpine.store('case').documents || [];
        },

        // Get entity type options for filter
        get entityTypeOptions() {
            return [
                { value: 'all', label: 'All Entities' },
                { value: 'UK_JUDGE', label: 'Judges' },
                { value: 'UK_LOCAL_AUTHORITY', label: 'Local Authorities' },
                { value: 'UK_POLICE_FORCE', label: 'Police Forces' },
                { value: 'UK_COURT', label: 'Courts' },
                { value: 'SOLICITOR_FIRM', label: 'Solicitor Firms' },
                { value: 'CASE_NUMBER', label: 'Case Numbers' }
            ];
        }
    }));
}
