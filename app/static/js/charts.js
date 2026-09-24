/**
 * DNAura — Chart.js Interactive Visualization Engine
 */

const GenomixCharts = {
    theme: {
        textColor: '#94A3B8',
        gridColor: 'rgba(255, 255, 255, 0.06)',
        fontFamily: 'Inter, sans-serif'
    },

    updateThemeColors: function(themeName) {
        if (themeName === 'light') {
            this.theme.textColor = '#334155';
            this.theme.gridColor = 'rgba(0, 0, 0, 0.08)';
        } else {
            this.theme.textColor = '#94A3B8';
            this.theme.gridColor = 'rgba(255, 255, 255, 0.06)';
        }
    },

    // 1. Nucleotide Distribution Bar Chart
    renderNucleotideBar: function(canvasId, barData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !barData) return;

        return new Chart(ctx, {
            type: 'bar',
            data: barData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        titleColor: '#F8FAFC',
                        bodyColor: '#94A3B8',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { color: this.theme.gridColor },
                        ticks: { color: this.theme.textColor, font: { family: this.theme.fontFamily } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: this.theme.gridColor },
                        ticks: { color: this.theme.textColor, font: { family: this.theme.fontFamily } }
                    }
                }
            }
        });
    },

    // 2. Nucleotide Percentage Donut
    renderNucleotideDoughnut: function(canvasId, donutData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !donutData) return;

        return new Chart(ctx, {
            type: 'doughnut',
            data: donutData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: this.theme.textColor, font: { family: this.theme.fontFamily, size: 12 }, padding: 14 }
                    },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        titleColor: '#F8FAFC',
                        bodyColor: '#94A3B8',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                }
            }
        });
    },

    // 3. Functional Classification Radar Chart
    renderClassificationRadar: function(canvasId, radarData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !radarData) return;

        return new Chart(ctx, {
            type: 'radar',
            data: radarData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: this.theme.textColor, font: { family: this.theme.fontFamily } }
                    }
                },
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        pointLabels: { color: this.theme.textColor, font: { family: this.theme.fontFamily, size: 11 } },
                        ticks: { backdropColor: 'transparent', color: this.theme.textColor }
                    }
                }
            }
        });
    },

    // 4. Pairwise Similarity Comparison Horizontal Bar
    renderSimilarityComparison: function(canvasId, simData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !simData) return;

        return new Chart(ctx, {
            type: 'bar',
            data: simData,
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        max: 100,
                        grid: { color: this.theme.gridColor },
                        ticks: { color: this.theme.textColor, font: { family: 'JetBrains Mono, monospace' } }
                    },
                    y: {
                        grid: { color: this.theme.gridColor },
                        ticks: { color: this.theme.textColor }
                    }
                }
            }
        });
    },

    // 5. Mutation Distribution Map
    renderMutationDistributionMap: function(canvasId, mapData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !mapData) return;

        return new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: mapData.datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: this.theme.textColor, font: { family: this.theme.fontFamily } }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const pt = context.raw;
                                return pt.label || `Coordinate: ${pt.x} bp`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: mapData.sequence_length || 100,
                        title: { display: true, text: 'Sequence Coordinate (bp)', color: this.theme.textColor },
                        grid: { color: this.theme.gridColor },
                        ticks: { color: this.theme.textColor }
                    },
                    y: {
                        min: 0.5,
                        max: 3.5,
                        ticks: {
                            stepSize: 1,
                            callback: function(val) {
                                if (val === 1) return 'Substitutions';
                                if (val === 2) return 'Insertions';
                                if (val === 3) return 'Deletions';
                                return '';
                            },
                            color: this.theme.textColor
                        },
                        grid: { color: this.theme.gridColor }
                    }
                }
            }
        });
    },

    // 6. GC vs AT Content Donut Chart
    renderGCvsAT: function(canvasId, gcData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !gcData) return;

        return new Chart(ctx, {
            type: 'doughnut',
            data: gcData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: this.theme.textColor, font: { family: this.theme.fontFamily, size: 12 }, padding: 14 }
                    },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        titleColor: '#F8FAFC',
                        bodyColor: '#94A3B8',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                }
            }
        });
    },

    // 7. Top 10 Trinucleotide (3-mer) Frequencies Bar Chart
    renderKmerBar: function(canvasId, kmerData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx || !kmerData) return;

        return new Chart(ctx, {
            type: 'bar',
            data: kmerData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0F172A',
                        titleColor: '#F8FAFC',
                        bodyColor: '#94A3B8',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { color: this.theme.gridColor },
                        ticks: { color: this.theme.textColor, font: { family: 'JetBrains Mono, monospace' } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: this.theme.gridColor },
                        ticks: { color: this.theme.textColor, font: { family: this.theme.fontFamily } }
                    }
                }
            }
        });
    },

    // 8. Alias for Mutation Map
    renderMutationMap: function(canvasId, mapData) {
        return this.renderMutationDistributionMap(canvasId, mapData);
    }
};

window.addEventListener("themeChanged", (e) => {
    const newTheme = e.detail && e.detail.theme ? e.detail.theme : 'dark';
    GenomixCharts.updateThemeColors(newTheme);
    if (typeof Chart !== "undefined") {
        Object.keys(Chart.instances).forEach(id => {
            const chart = Chart.instances[id];
            if (chart && chart.options && chart.options.scales) {
                if (chart.options.scales.x && chart.options.scales.x.ticks) {
                    chart.options.scales.x.ticks.color = GenomixCharts.theme.textColor;
                }
                if (chart.options.scales.y && chart.options.scales.y.ticks) {
                    chart.options.scales.y.ticks.color = GenomixCharts.theme.textColor;
                }
                chart.update();
            }
        });
    }
});

