
/**
 * Abstract Generator Frontend
 *
 * Provides the frontend interface for the abstract generator web app. Handles user
 * input as seed prompts, communicates with the backend, and displays the generated academic
 * article abstract with animations.
 *
 * @author Yahia Nassab
 */

"use strict"

const flashRemovalTimeMilliseconds = 500;
let lockGeneration = false;

const getDataAPIEndpoint = 'https://sghqbi8lll.execute-api.us-east-1.amazonaws.com/default/';

/**
 * Initializes the application when the DOM is fully loaded.
 * Sets up event listeners for the generate button and seed input field.
 */
document.addEventListener('DOMContentLoaded', async () => {
    const generateButton = document.querySelector('#generate-button');
    const seedInput = document.querySelector('#seed-prompt');
    generateButton.addEventListener('click', handleGenerate);
    seedInput.addEventListener('keydown', (event) => {
        if (event.code === 'Enter') {
            handleGenerate();
        }
    });
    await awakenFromDeepSleep();
})

/**
 * Awakens the backend server from deep sleep.
 *
 * Makes a POST request to the backend API to wake it up. If successful, the loading screen is hidden
 * and the application container is displayed. If unsuccessful, an error message is shown on the loading screen.
 *
 * @returns {Promise<void>}
 */
async function awakenFromDeepSleep() {
    const loadingScreenContainer = document.querySelector('#loading-screen-container');
    const applicationContainer = document.querySelector('#application-container');
    try {
        const response = await fetch(getDataAPIEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                wakeUp: 'Hello from Abstract Generator frontend!',
            })
        });

        if (response.ok) {
            loadingScreenContainer.style.display = 'none';
            applicationContainer.style.display = 'block';
        } else {
            const { output } = await response.json();
            console.error(`Error: response status of ${response.status}\n${JSON.stringify(output, null, 2)}`);
            showLoadingScreenError();
        }
    } catch (error) {
        console.error('Fetch failed:', error);
        showLoadingScreenError();
    }
}

/**
 * Displays an error message on the loading screen.
 *
 * Updates the loading screen text to inform the user that the server connection failed.
 */
function showLoadingScreenError() {
    const loadingScreenText = document.querySelector('#loading-screen-text');
    const loadingScreenContainer = document.querySelector('#loading-screen-container');

    // Change loading screen message with a vanish and phase-in effect
    loadingScreenContainer.classList.remove('show');
    loadingScreenText.innerText = 'Unable to connect to the server. Please try again later.';
    setTimeout(() => {
        loadingScreenContainer.classList.add('show');
    }, 100);
}

/**
 * Handles the abstract generation process when triggered by user interaction.
 *
 * This function:
 * - Validates user input
 * - Makes API requests to the ML backend
 * - Manages loading states and visual feedback
 * - Displays generated abstracts with typewriter effect
 * - Handles errors gracefully
 *
 * @returns {Promise<void>}
 *
 * @throws {Error} Network errors or API failures are caught and handled internally
 *
 */
async function handleGenerate() {
    if (lockGeneration) { return }

    const responseElem = document.querySelector('#response-output');
    const loadingDotContainer = document.querySelector('#loading-dot-container');
    const seed = document.querySelector('#seed-prompt').value;

    flashReponseBackground();

    if (seed.trim() === '') {
        responseElem.innerText = 'Please enter a seed in the input field above!';
        return;
    } else {
        loadingDotContainer.style.display = 'flex';
        responseElem.innerText = '';
        lockGeneration = true;
    }

    try {
        const response = await fetch(getDataAPIEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                seed: seed,
            })
        })
        const { output } = await response.json()

        if (response.status != 200) {
            handleFetchError(`Error: response status of ${response.status}`);
        } else {
            flashReponseBackground();
            loadingDotContainer.style.display = 'none';
            typewriterEffect(responseElem, output);
        }
    } catch (error) {
        handleFetchError(error);
    }
}

/**
 * Handles errors that occur during API requests or processing.
 *
 * Provides user-friendly error messaging and resets the UI to a clean state
 * when generation fails.
 *
 * @param {Error|string} error - The error object or message to handle
 *
 * @example
 * handleFetchError(new Error("Network timeout"));
 * handleFetchError("Custom error message");
 */
function handleFetchError(error) {
    console.error(error);
    const responseElem = document.querySelector('#response-output');
    const loadingDotContainer = document.querySelector('#loading-dot-container');
    flashReponseBackground();
    loadingDotContainer.style.display = 'none';
    responseElem.innerText = 'There was an error making your request! Please try again later.';
}

/**
 * Creates a visual flash effect on the response container background.
 *
 * Adds a CSS class for the flash animation and automatically removes it
 * after the specified duration to provide visual feedback for user actions.
 *
 */
function flashReponseBackground() {
    let backgroundFlashClass = 'response-background-flash';
    const responseElemContainer = document.querySelector('#response-output-container');
    responseElemContainer.classList.add(backgroundFlashClass);
    setTimeout(() => {
        responseElemContainer.classList.remove(backgroundFlashClass);
    }, flashRemovalTimeMilliseconds);
}

/**
 * Displays text with a typewriter animation effect.
 *
 * Characters are revealed progressively to create an engaging user experience
 * when displaying generated abstracts. HTML content is periodically re-rendered
 * to ensure proper display of tags and special characters.
 *
 * @param {HTMLElement} element - The DOM element to display the text in
 * @param {string} text - The text content to display with typewriter effect
 * @param {number} [delayMilliseconds=5] - Delay between each character in milliseconds
 *
 */
function typewriterEffect(element, text, delayMilliseconds = 5) {
    let i = 0;
    let responseSoFar = '';

    /**
     * Internal recursive function that handles character-by-character text display.
     * Releases the generation lock when complete.
     */
    function typeChunk() {
        if (i < text.length) {
            element.innerHTML += text[i];
            responseSoFar += text[i];
            i++;
            // Periodically re-render HTML to ensure proper display
            if (i % 25 === 0 || i === text.length) {
                element.innerHTML = responseSoFar;
            }
            setTimeout(typeChunk, delayMilliseconds);
        } else {
            // Release generation lock when animation completes
            lockGeneration = false;
        }
    }

    typeChunk();
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        handleGenerate,
        handleFetchError,
        flashReponseBackground,
        typewriterEffect,
        // State management for testing
        getState: () => ({
            lockGeneration,
            flashRemovalTimeMilliseconds,
            getDataAPIEndpoint
        }),
        setState: (state) => {
            if (state.lockGeneration !== undefined) lockGeneration = state.lockGeneration;
        },
        // Constants for testing
        constants: {
            flashRemovalTimeMilliseconds,
            getDataAPIEndpoint
        }
    };
}
