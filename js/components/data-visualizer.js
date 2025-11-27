// Data Visualizer Component
function registerDataVisualizer() {
    Alpine.data('dataVisualizerComponent', () => ({
        charts: {},

        initCharts() {
            this.$nextTick(() => {
                this.createViolationsChart();
                this.createTasksChart();
                this.createTimelineChart();
                this.createEntityChart();
            });
        },

        createViolationsChart() {
            const ctx = document.getElementById('violationsSeverityChart');
            if (!ctx) return;
            const stats = Alpine.store('case').violationStats;
            this.charts.violations = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Critical', 'High', 'Medium', 'Low'],
                    datasets: [{
                        data: [stats.critical, stats.high, stats.medium, stats.low],
                        backgroundColor: ['#DC2626', '#F59E0B', '#C9AE5D', '#22C55E'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: '#9CA3AF', font: { family: 'JetBrains Mono' } } }
                    }
                }
            });
        },

        createTasksChart() {
            const ctx = document.getElementById('tasksStatusChart');
            if (!ctx) return;
            const stats = Alpine.store('case').taskStats;
            this.charts.tasks = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['To Do', 'In Progress', 'Review', 'Completed'],
                    datasets: [{
                        data: [stats.todo, stats.inProgress, stats.review, stats.completed],
                        backgroundColor: ['#6B7280', '#C9AE5D', '#8B7B3A', '#22C55E'],
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { grid: { color: '#2a2f35' }, ticks: { color: '#9CA3AF', font: { family: 'JetBrains Mono' } } },
                        x: { grid: { display: false }, ticks: { color: '#9CA3AF', font: { family: 'JetBrains Mono' } } }
                    }
                }
            });
        },

        createTimelineChart() {
            const ctx = document.getElementById('timelineChart');
            if (!ctx) return;
            const timeline = Alpine.store('case').timeline;
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const eventsByMonth = {};
            timeline.forEach(event => {
                const date = new Date(event.date);
                const monthKey = months[date.getMonth()];
                eventsByMonth[monthKey] = (eventsByMonth[monthKey] || 0) + 1;
            });
            this.charts.timeline = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Object.keys(eventsByMonth).length > 0 ? Object.keys(eventsByMonth) : months.slice(0, 6),
                    datasets: [{
                        label: 'Events',
                        data: Object.keys(eventsByMonth).length > 0 ? Object.values(eventsByMonth) : [2, 5, 3, 8, 4, 6],
                        borderColor: '#C9AE5D',
                        backgroundColor: 'rgba(201, 174, 93, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { grid: { color: '#2a2f35' }, ticks: { color: '#9CA3AF', font: { family: 'JetBrains Mono' } } },
                        x: { grid: { display: false }, ticks: { color: '#9CA3AF', font: { family: 'JetBrains Mono' } } }
                    }
                }
            });
        },

        createEntityChart() {
            const ctx = document.getElementById('entityChart');
            if (!ctx) return;
            const uniqueEntities = Alpine.store('case').uniqueEntities || [];
            const byType = {};
            uniqueEntities.forEach(e => { byType[e.type] = (byType[e.type] || 0) + 1; });
            const typeLabels = {
                'UK_JUDGE': 'Judges', 'UK_LOCAL_AUTHORITY': 'Local Authorities',
                'UK_POLICE_FORCE': 'Police Forces', 'UK_COURT': 'Courts',
                'CASE_NUMBER': 'Case Numbers', 'SOLICITOR_FIRM': 'Solicitors', 'DATE': 'Dates'
            };
            const typeColors = {
                'UK_JUDGE': 'rgba(201, 174, 93, 0.8)', 'UK_LOCAL_AUTHORITY': 'rgba(139, 123, 58, 0.8)',
                'UK_POLICE_FORCE': 'rgba(107, 114, 128, 0.8)', 'UK_COURT': 'rgba(212, 195, 106, 0.8)',
                'CASE_NUMBER': 'rgba(156, 163, 175, 0.8)', 'SOLICITOR_FIRM': 'rgba(181, 166, 66, 0.8)',
                'DATE': 'rgba(69, 77, 87, 0.8)'
            };
            const types = Object.keys(byType).filter(t => t !== 'DATE');
            this.charts.entity = new Chart(ctx, {
                type: 'polarArea',
                data: {
                    labels: types.map(t => typeLabels[t] || t),
                    datasets: [{
                        data: types.map(t => byType[t]),
                        backgroundColor: types.map(t => typeColors[t] || 'rgba(156, 163, 175, 0.7)')
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'right', labels: { color: '#9CA3AF', font: { family: 'JetBrains Mono' } } } }
                }
            });
        },

        refreshCharts() {
            Object.values(this.charts).forEach(chart => chart.destroy());
            this.charts = {};
            this.initCharts();
        }
    }));
}
