(function () {
    const palette = [
        "#16A085",
        "#2ECC71",
        "#F4B740",
        "#FF6B6B",
        "#5DADE2",
        "#AF7AC5",
        "#48C9B0",
        "#F8C471",
        "#85929E",
        "#76D7C4"
    ];

    Chart.defaults.font.family = "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    Chart.defaults.color = "#6B7280";
    Chart.defaults.borderColor = "rgba(229, 234, 240, 0.78)";

    function readData(scriptId) {
        const element = document.getElementById(scriptId);
        if (!element) {
            return null;
        }
        try {
            return JSON.parse(element.textContent);
        } catch (error) {
            return null;
        }
    }

    function getCanvas(canvasId) {
        const canvas = document.getElementById(canvasId);
        return canvas ? canvas.getContext("2d") : null;
    }

    function renderEmpty(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) {
            return;
        }
        const parent = canvas.closest(".chart-box");
        if (parent && !parent.querySelector(".empty-state")) {
            const empty = document.createElement("div");
            empty.className = "empty-state";
            empty.textContent = "No data available for this chart.";
            canvas.replaceWith(empty);
        }
    }

    function hasValues(values) {
        return Array.isArray(values) && values.some((value) => Number(value) > 0);
    }

    function baseOptions(extra) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        boxWidth: 12,
                        boxHeight: 12,
                        padding: 16,
                        useBorderRadius: true,
                        borderRadius: 8
                    },
                    position: "bottom"
                },
                tooltip: {
                    backgroundColor: "#1E2A38",
                    padding: 12,
                    cornerRadius: 14,
                    titleColor: "#FFFFFF",
                    bodyColor: "#DDE7F0"
                }
            },
            ...extra
        };
    }

    window.expenseCharts = {
        renderPie(scriptId, canvasId, label) {
            const data = readData(scriptId);
            const ctx = getCanvas(canvasId);
            if (!data || !ctx || !hasValues(data.values)) {
                renderEmpty(canvasId);
                return;
            }
            new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: label || "Expenses",
                        data: data.values,
                        backgroundColor: palette,
                        borderColor: "rgba(255,255,255,0.92)",
                        borderWidth: 3,
                        hoverOffset: 8
                    }]
                },
                options: baseOptions({
                    cutout: "64%"
                })
            });
        },
        renderBar(scriptId, canvasId, label) {
            const data = readData(scriptId);
            const ctx = getCanvas(canvasId);
            if (!data || !ctx || !hasValues(data.values)) {
                renderEmpty(canvasId);
                return;
            }
            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: label || "Expenses",
                        data: data.values,
                        backgroundColor: "rgba(22, 160, 133, 0.78)",
                        borderColor: "#16A085",
                        borderRadius: 12,
                        borderSkipped: false
                    }]
                },
                options: baseOptions({
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: "#6B7280" }
                        },
                        y: {
                            beginAtZero: true,
                            border: { display: false },
                            grid: { color: "rgba(229, 234, 240, 0.78)" },
                            ticks: { color: "#6B7280" }
                        }
                    },
                    plugins: {
                        ...baseOptions({}).plugins,
                        legend: { display: false }
                    }
                })
            });
        },
        renderLine(scriptId, canvasId, label) {
            const data = readData(scriptId);
            const ctx = getCanvas(canvasId);
            if (!data || !ctx || !hasValues(data.values)) {
                renderEmpty(canvasId);
                return;
            }
            new Chart(ctx, {
                type: "line",
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: label || "Daily expenses",
                        data: data.values,
                        borderColor: "#16A085",
                        backgroundColor: "rgba(22, 160, 133, 0.14)",
                        borderWidth: 3,
                        fill: true,
                        pointBackgroundColor: "#FFFFFF",
                        pointBorderColor: "#16A085",
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        tension: 0.38
                    }]
                },
                options: baseOptions({
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: "#6B7280" }
                        },
                        y: {
                            beginAtZero: true,
                            border: { display: false },
                            grid: { color: "rgba(229, 234, 240, 0.78)" },
                            ticks: { color: "#6B7280" }
                        }
                    }
                })
            });
        }
    };
})();
