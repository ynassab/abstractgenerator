/**
 * Load Animations Controller
 *
 * Provides scroll-based animation functionality using the Intersection Observer API.
 * Detects when elements with specific animation classes enter the viewport and triggers
 * their reveal animations by adding the "show" class.
 *
 * @author Yahia Nassab
 */

/**
 * Initializes scroll-based animations when the DOM is fully loaded.
 *
 * Sets up an Intersection Observer to monitor elements with animation classes
 * and triggers their animations when they enter the viewport.
 */
document.addEventListener("DOMContentLoaded", () => {
    /**
     * Callback function for Intersection Observer.
     *
     * Processes all elements that enter or exit the viewport and adds the "show"
     * class to elements that are currently intersecting (visible).
     *
     * @param {IntersectionObserverEntry[]} entries - Array of intersection entries
     *
     */
    const intersectionCallback = (entries) => {
        for (const entry of entries) { // Loop over all elements that either enter or exit the view
            if (entry.isIntersecting) { // True when the element is in view
                entry.target.classList.add("show");
            }
        }
    }

    const observer = new IntersectionObserver(intersectionCallback);
    const items = document.querySelectorAll(
        ".load-left, .load-right, .load-up, .load-down, .load-down-fast,"
        + " .load-left-then-out, .phase-in, .phase-in-delay-1, .phase-in-delay-2, .phase-out"
    );
    for (const item of items) {
        observer.observe(item);
    }
});
