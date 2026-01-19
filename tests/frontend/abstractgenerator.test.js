/**
 * @jest-environment jsdom
 */

let moduleExports;

function loadModuleWithDOM() {
    jest.resetModules();

    // Load the module
    moduleExports = require('../../src/frontend/abstractgenerator/scripts/abstractgenerator.js');
}

beforeEach(() => {
    document.body.innerHTML = `
        <div id="loading-screen-container" class="phase-in-delay-1">
            <div id="loading-screen-text-container">
                <p id="loading-screen-text">Awakening from deep sleep...</p>
            </div>
        </div>
        <div id="seed-prompt-container">
            <input id="seed-prompt" placeholder="Enter seed here..." value="">
            <button id="generate-button">Generate</button>
        </div>
        <div id="response-output-container">
            <div id="loading-dot-container" style="display: none;">
                <div class="loading-dot" id="loading-dot-1"></div>
                <div class="loading-dot" id="loading-dot-2"></div>
                <div class="loading-dot" id="loading-dot-3"></div>
            </div>
            <p id="response-output"></p>
        </div>
    `;

    // Mock fetch globally
    global.fetch = jest.fn();

    // Mock console.error to avoid noise in tests
    jest.spyOn(console, 'error').mockImplementation(() => {});

    loadModuleWithDOM();
});

afterEach(() => {
    jest.restoreAllMocks();
    jest.clearAllTimers();
});

describe('Abstract Generator Frontend', () => {
    describe('Event listeners', () => {
        test('DOMContentLoaded block executes and sets up event listeners', () => {
            const generateButton = document.querySelector('#generate-button');
            const seedInput = document.querySelector('#seed-prompt');

            const addEventListenerSpy = jest.spyOn(document, "addEventListener");
            const buttonListenerSpy = jest.spyOn(generateButton, "addEventListener");
            const inputListenerSpy = jest.spyOn(seedInput, "addEventListener");

            document.dispatchEvent(new Event("DOMContentLoaded"));

            expect(buttonListenerSpy).toHaveBeenCalledWith("click", expect.any(Function));
            expect(inputListenerSpy).toHaveBeenCalledWith("keydown", expect.any(Function));
        });
    });

    describe('handleGenerate', () => {
        beforeEach(() => {
            jest.useFakeTimers();
        });

        afterEach(() => {
            jest.useRealTimers();
        });

        test('returns early if generation is locked', async () => {
            moduleExports.setState({ lockGeneration: true });
            global.fetch = jest.fn();

            await moduleExports.handleGenerate();

            expect(global.fetch).not.toHaveBeenCalled();
        });

        test('shows error message for empty seed', async () => {
            const seedInput = document.querySelector('#seed-prompt');
            const responseElem = document.querySelector('#response-output');

            seedInput.value = '';

            await moduleExports.handleGenerate();

            expect(responseElem.innerText).toBe('Please enter a seed in the input field above!');
        });

        test('shows error message for whitespace-only seed', async () => {
            const seedInput = document.querySelector('#seed-prompt');
            const responseElem = document.querySelector('#response-output');

            seedInput.value = '   ';

            await moduleExports.handleGenerate();

            expect(responseElem.innerText).toBe('Please enter a seed in the input field above!');
        });

        test('handles non-200 response status', async () => {
            const seedInput = document.querySelector('#seed-prompt');
            const responseElem = document.querySelector('#response-output');

            seedInput.value = 'test seed';

            global.fetch.mockResolvedValueOnce({
                status: 500,
                json: async () => ({ output: 'error' })
            });

            await moduleExports.handleGenerate();

            expect(responseElem.innerText).toBe('There was an error making your request! Please try again later.');
        });

        test('handles fetch error', async () => {
            const seedInput = document.querySelector('#seed-prompt');
            const responseElem = document.querySelector('#response-output');

            seedInput.value = 'test seed';

            global.fetch.mockRejectedValueOnce(new Error('Network error'));

            await moduleExports.handleGenerate();

            expect(responseElem.innerText).toBe('There was an error making your request! Please try again later.');
        });

        test('shows loading state during generation', async () => {
            const seedInput = document.querySelector('#seed-prompt');
            const responseElem = document.querySelector('#response-output');
            const loadingDotContainer = document.querySelector('#loading-dot-container');

            seedInput.value = 'test seed';

            let resolvePromise;
            const fetchPromise = new Promise(resolve => {
                resolvePromise = resolve;
            });
            global.fetch.mockReturnValueOnce(fetchPromise);

            const generatePromise = moduleExports.handleGenerate();

            // Check loading state before fetch resolves
            expect(loadingDotContainer.style.display).toBe('flex');
            expect(responseElem.innerText).toBe('');
            expect(moduleExports.getState().lockGeneration).toBe(true);

            // Resolve the fetch
            resolvePromise({
                status: 200,
                json: async () => ({ output: 'test output' })
            });

            await generatePromise;
        });
    });

    describe('handleFetchError', () => {
        test('displays error message and resets UI state', () => {
            const responseElem = document.querySelector('#response-output');
            const loadingDotContainer = document.querySelector('#loading-dot-container');

            // Set initial state
            loadingDotContainer.style.display = 'flex';

            moduleExports.handleFetchError('Test error');

            expect(responseElem.innerText).toBe('There was an error making your request! Please try again later.');
            expect(loadingDotContainer.style.display).toBe('none');
            expect(console.error).toHaveBeenCalledWith('Test error');
        });

        test('handles Error objects', () => {
            const error = new Error('Network timeout');

            moduleExports.handleFetchError(error);

            expect(console.error).toHaveBeenCalledWith(error);
        });
    });

    describe('flashReponseBackground', () => {
        beforeEach(() => {
            jest.useFakeTimers();
        });

        afterEach(() => {
            jest.useRealTimers();
        });

        test('adds and removes flash class', () => {
            const responseContainer = document.querySelector('#response-output-container');

            moduleExports.flashReponseBackground();

            expect(responseContainer.classList.contains('response-background-flash')).toBe(true);

            jest.advanceTimersByTime(500);

            expect(responseContainer.classList.contains('response-background-flash')).toBe(false);
        });

        test('uses correct timeout duration', () => {
            const responseContainer = document.querySelector('#response-output-container');

            moduleExports.flashReponseBackground();

            expect(responseContainer.classList.contains('response-background-flash')).toBe(true);

            // Before timeout
            jest.advanceTimersByTime(499);
            expect(responseContainer.classList.contains('response-background-flash')).toBe(true);

            // After timeout
            jest.advanceTimersByTime(1);
            expect(responseContainer.classList.contains('response-background-flash')).toBe(false);
        });
    });

    describe('typewriterEffect', () => {
        beforeEach(() => {
            jest.useFakeTimers();
        });

        afterEach(() => {
            jest.useRealTimers();
        });

        test('displays text character by character', () => {
            const element = document.createElement('div');
            const text = 'Hello';

            moduleExports.typewriterEffect(element, text, 10);

            // First character appears immediately
            expect(element.innerHTML).toBe('H');

            // After first delay
            jest.advanceTimersByTime(10);
            expect(element.innerHTML).toBe('He');

            // After second delay
            jest.advanceTimersByTime(10);
            expect(element.innerHTML).toBe('Hel');

            // Complete the animation
            jest.advanceTimersByTime(30);
            expect(element.innerHTML).toBe('Hello');
        });

        test('uses default delay when not specified', () => {
            const element = document.createElement('div');
            const text = 'Hi';

            moduleExports.typewriterEffect(element, text);

            // First character appears immediately
            expect(element.innerHTML).toBe('H');

            // After default delay (5ms)
            jest.advanceTimersByTime(5);
            expect(element.innerHTML).toBe('Hi');
        });

        test('releases generation lock when complete', () => {
            const element = document.createElement('div');
            const text = 'Test';

            moduleExports.setState({ lockGeneration: true });
            moduleExports.typewriterEffect(element, text, 1);

            expect(moduleExports.getState().lockGeneration).toBe(true);

            // Complete the animation
            jest.advanceTimersByTime(10);

            expect(moduleExports.getState().lockGeneration).toBe(false);
        });

        test('re-renders HTML every 25 characters', () => {
            const element = document.createElement('div');
            // Create text longer than 25 characters
            const text = 'A'.repeat(30);

            const setInnerHTMLSpy = jest.spyOn(element, 'innerHTML', 'set');

            moduleExports.typewriterEffect(element, text, 1);

            // Advance to trigger HTML re-render at character 25
            jest.advanceTimersByTime(25);

            // Should have been set multiple times due to progressive updates + re-render
            expect(setInnerHTMLSpy.mock.calls.length).toBeGreaterThan(25);
        });

        test('handles empty text', () => {
            const element = document.createElement('div');
            const text = '';

            moduleExports.setState({ lockGeneration: true });
            moduleExports.typewriterEffect(element, text);

            // Should immediately release lock
            expect(moduleExports.getState().lockGeneration).toBe(false);
            expect(element.innerHTML).toBe('');
        });
    });

    describe('State management', () => {
        test('getState returns current state', () => {
            const state = moduleExports.getState();

            expect(state).toHaveProperty('lockGeneration');
            expect(state).toHaveProperty('flashRemovalTimeMilliseconds');
            expect(state).toHaveProperty('getDataAPIEndpoint');
        });

        test('setState updates lockGeneration', () => {
            moduleExports.setState({ lockGeneration: true });
            expect(moduleExports.getState().lockGeneration).toBe(true);

            moduleExports.setState({ lockGeneration: false });
            expect(moduleExports.getState().lockGeneration).toBe(false);
        });

        test('setState ignores undefined values', () => {
            const initialState = moduleExports.getState().lockGeneration;

            moduleExports.setState({ lockGeneration: undefined });

            expect(moduleExports.getState().lockGeneration).toBe(initialState);
        });
    });

    describe('Constants', () => {
        test('constants are accessible for testing', () => {
            expect(moduleExports.constants.flashRemovalTimeMilliseconds).toBe(500);
            expect(moduleExports.constants.getDataAPIEndpoint).toContain('execute-api.us-east-1.amazonaws.com');
        });
    });
});
