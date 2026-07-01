(function () {
  const links = document.querySelectorAll(".toc a");
  if (!links.length) return;
  const headings = Array.from(document.querySelectorAll(".legalContent h2"));
  const byId = new Map(Array.from(links).map((a) => [a.getAttribute("href").slice(1), a]));
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const link = byId.get(entry.target.id);
      if (!link) return;
      if (entry.isIntersecting) {
        links.forEach((a) => a.classList.remove("active"));
        link.classList.add("active");
      }
    });
  }, { rootMargin: "-20% 0px -70% 0px", threshold: 0 });
  headings.forEach((h) => observer.observe(h));
})();
