(function () {
  const MIN_WORDS = Number(document.body.dataset.minWords || 120);
  const TARGET_WORDS = Number(document.body.dataset.targetWords || 170);

  function wordCount(text) {
    const matches = text.trim().match(/\b[\p{L}\p{N}]+(?:[-'][\p{L}\p{N}]+)?\b/gu);
    return matches ? matches.length : 0;
  }

  function updateCounter(textarea) {
    const counter = document.querySelector(`[data-counter-for="${textarea.id}"]`);
    if (!counter) return;
    const count = wordCount(textarea.value);
    counter.textContent = `${count} Wörter`;
    counter.classList.toggle("good", count >= MIN_WORDS);
    counter.classList.toggle("warn", count > 0 && count < MIN_WORDS);
  }

  document.querySelectorAll("textarea[data-track-words]").forEach((textarea) => {
    updateCounter(textarea);
    textarea.addEventListener("input", () => updateCounter(textarea));
  });

  document.querySelectorAll("[data-toggle-sample]").forEach((button) => {
    button.addEventListener("click", () => {
      const sample = document.getElementById(button.dataset.toggleSample);
      if (!sample) return;
      sample.classList.toggle("visible");
      button.textContent = sample.classList.contains("visible") ? "Musterlösung ausblenden" : "Musterlösung anzeigen";
    });
  });

  document.querySelectorAll("[data-reset-writing]").forEach((button) => {
    button.addEventListener("click", () => {
      const textarea = document.getElementById(button.dataset.resetWriting);
      if (!textarea) return;
      textarea.value = "";
      updateCounter(textarea);
      textarea.focus();
    });
  });

  document.querySelectorAll("[data-score-group]").forEach((button) => {
    button.addEventListener("click", () => {
      const group = button.dataset.scoreGroup;
      const checks = Array.from(document.querySelectorAll(`input[data-check="${group}"]`));
      const score = checks.filter((item) => item.checked).length;
      const target = document.querySelector(`[data-score-result="${group}"]`);
      if (!target) return;
      const max = checks.length;
      let message = "Erst überarbeiten, dann mit der Musterlösung vergleichen.";
      if (score >= Math.ceil(max * .8)) message = "Gute Grundlage. Vergleiche jetzt gezielt Formulierungen und Bildwirkung.";
      else if (score >= Math.ceil(max * .55)) message = "Solide, aber mindestens zwei Punkte sollten noch genauer werden.";
      target.textContent = `${score} / ${max} Kriterien erfüllt. ${message}`;
      target.classList.add("visible");
    });
  });

  document.querySelectorAll("[data-fill-outline]").forEach((button) => {
    button.addEventListener("click", () => {
      const textarea = document.getElementById(button.dataset.fillOutline);
      if (!textarea || textarea.value.trim()) return;
      textarea.value = [
        "Einleitung: Auf dem Bild ist ... zu sehen. Die Szene spielt vermutlich ...",
        "",
        "Hauptteil: Im Vordergrund ... Im Mittelgrund ... Im Hintergrund ... Auffällig ist ...",
        "",
        "Bildwirkung/Deutung: Die Szene wirkt ..., weil ... Möglicherweise soll das Bild zeigen, dass ..."
      ].join("\n");
      updateCounter(textarea);
      textarea.focus();
    });
  });

  document.querySelectorAll("[data-copy-words]").forEach((button) => {
    button.addEventListener("click", async () => {
      const words = Array.from(document.querySelectorAll(".word")).map((el) => el.textContent.trim()).join(", ");
      try {
        await navigator.clipboard.writeText(words);
        button.textContent = "Wortschatz kopiert";
        setTimeout(() => { button.textContent = "Wortschatz kopieren"; }, 1600);
      } catch {
        button.textContent = "Kopieren nicht möglich";
      }
    });
  });
})();
