function draw() {
    const selected = [...document.querySelectorAll(".participant-row input:checked")]
        .map(i => parseInt(i.value));

    if (selected.length < 2) {
        alert("Selecione ao menos 2 participantes");
        return;
    }

    function toggleFullscreen() {
          if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
          } else {
                document.exitFullscreen();
          }
     }

    const qty = parseInt(document.getElementById("qty").value);

    fetch("/draw", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: selected, qty })
    })
    .then(r => r.json())
    .then(data => {
        const result = document.getElementById("result");
        result.innerHTML = "";

        data.forEach((p, i) => {
            setTimeout(() => {
                const div = document.createElement("div");
                div.innerHTML = `
                    <img src="${p.photo}">
                    <p>${p.name}</p>
                `;
                result.appendChild(div);
            }, i * 1200); // suspense maior
        });
    });
    
    document.addEventListener("click", e => {
    console.log("CLICADO:", e.target);
});
}
