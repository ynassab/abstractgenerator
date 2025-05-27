document.addEventListener("DOMContentLoaded", () => {
    const intersectionCallback = (entries) => {
        for (const entry of entries) { // Loop over all elements that either enter or exit the view
            if (entry.isIntersecting) { // True when the element is in view
                entry.target.classList.add("show");
            }
        }
    }

    const observer = new IntersectionObserver(intersectionCallback);
    const items = document.querySelectorAll(".load-left, .load-right, .load-up, .load-down, .load-down-fast, .load-left-then-out, .phase-in, .phase-in-delay-1, .phase-in-delay-2, .phase-out");
    for (const item of items) {
        observer.observe(item);
    }
});
