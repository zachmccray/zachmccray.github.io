// Start of file
const labels = ["2020", "2021", "2022", "2023", "2024", "2025"];
const booksPerYear = [44, 17, 26, 6, 26, 6];
const moviesPerYear = [null, null, null, 46, 107, 62];
const estimatedMovies = [51, 43, 62, 46, null, null];

const cumulativeBooks = booksPerYear.reduce((acc, val, i) => {
  acc.push((acc[i - 1] || 0) + val);
  return acc;
}, []);
const cumulativeMovies = moviesPerYear.reduce((acc, val, i) => {
  acc.push((acc[i - 1] || 0) + val);
  return acc;
}, []);

const softBlue = "rgba(103, 140, 255, 0.6)";
const softRed = "rgba(255, 99, 132, 0.6)";
const dashedRed = "rgba(255, 99, 132, 0.3)";
const fadedBlue = "rgba(103, 140, 255, 0.3)";
const fadedRed = "rgba(255, 99, 132, 0.3)";

function delayedDataset(label, data, color, delayIndex) {
  return {
    label,
    data,
    borderColor: color,
    backgroundColor: color,
    tension: 0.3,
    borderWidth: 2,
    fill: false,
    pointRadius: 3,
    pointHoverRadius: 6,
    animation: {
      delay: delayIndex * 300
    }
  };
}

window.addEventListener("load", function () {
  const ctx = document.getElementById("readingChart").getContext("2d");

  new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        delayedDataset("Books Read", booksPerYear, softBlue, 0),
        delayedDataset("Films Watched", moviesPerYear, softRed, 1),
        delayedDataset("Books (Cumulative)", cumulativeBooks, fadedBlue, 3),
        delayedDataset("Films (Cumulative)", cumulativeMovies, fadedRed, 4),
        {
          label: "Estimated Films (Pre-2023)",
          data: estimatedMovies,
          borderColor: dashedRed,
          borderDash: [5, 5],
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          animation: { delay: 2 * 300 }
        }
      ]
    },
    options: {
      responsive: true,
      animation: {
        duration: 1000,
        easing: 'easeOutQuart',
        delay(ctx) {
          const datasetIndex = ctx.datasetIndex;
          const dataIndex = ctx.dataIndex;
          return datasetIndex * 300 + dataIndex * 30;
        }
      },
      plugins: {
        legend: { display: true },
        tooltip: {
          backgroundColor: "rgba(255,255,255,0.95)",
          titleColor: "#333",
          bodyColor: "#444",
          borderColor: "#ccc",
          borderWidth: 1,
          cornerRadius: 6,
          padding: 10,
          callbacks: {
            label: function (context) {
              const val = context.raw;
              const prev = context.dataset.data[context.dataIndex - 1];
              let change = "";
              if (
                typeof val === "number" &&
                typeof prev === "number" &&
                context.dataIndex !== 0
              ) {
                const diff = val - prev;
                change = ` (${diff > 0 ? "+" : ""}${diff})`;
              }
              return `${context.dataset.label}: ${val}${change}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: "#555" },
          grid: { color: "#eee" }
        },
        x: {
          ticks: { color: "#555" },
          grid: { display: false }
        }
      }
    }
  });
});

function downloadChart() {
  const canvas = document.getElementById("readingChart");
  const link = document.createElement("a");
  link.download = "reading-movie-chart.png";
  link.href = canvas.toDataURL("image/png");
  link.click();
}

function exportCSV() {
  const rows = [
    ["Year", "Books Read", "Movies Watched", "Books (Cumulative)", "Movies (Cumulative)", "Estimated Movies (Pre-2023)"]
  ];

  for (let i = 0; i < labels.length; i++) {
    rows.push([
      labels[i],
      booksPerYear[i] ?? "",
      moviesPerYear[i] ?? "",
      cumulativeBooks[i] ?? "",
      cumulativeMovies[i] ?? "",
      estimatedMovies[i] ?? ""
    ]);
  }

  const csvContent = rows.map(e => e.join(",")).join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.setAttribute("href", URL.createObjectURL(blob));
  link.setAttribute("download", "reading-movie-data.csv");
  link.click();
}