async function loadHikes() {
    const response = await fetch('/data/hikes.csv');
    const csvText = await response.text();

    // Parse CSV into objects
    const lines = csvText.trim().split('\n');
    const headers = lines.shift().split(',');
    const hikes = lines.map(line => {
        const values = line.split(',');
        let hike = {};
        headers.forEach((header, i) => {
            hike[header] = values[i];
        });
        return hike;
    });

    displayHikes(hikes);
}

function displayHikes(hikes) {
    const container = document.getElementById('hike-list');
    hikes.forEach(hike => {
        const div = document.createElement('div');
        div.classList.add('hike-card');
        div.innerHTML = `
            <h3>${hike.Name}</h3>
            <p>${hike.Location}, ${hike.State}</p>
            <p>Distance: ${hike.Distance} mi | Elev Gain: ${hike['Elev Gain']} ft</p>
            <p>Difficulty: ${hike.Difficulty} | Rating: ${hike.Rating}</p>
            <a href="${hike.URL}" target="_blank">View on AllTrails</a>
        `;
        container.appendChild(div);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', loadHikes);
