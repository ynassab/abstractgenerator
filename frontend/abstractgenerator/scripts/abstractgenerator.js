"use strict"

const flashRemovalTimeMilliseconds = 500;
let generateLock = false;

const getDataAPIEndpoint = 'https://sghqbi8lll.execute-api.us-east-1.amazonaws.com/default/';

document.addEventListener('DOMContentLoaded', async () => {
    const generateButton = document.querySelector('#generate-button');
    const seedInput = document.querySelector('#seed-prompt');
    generateButton.addEventListener('click', handleGenerate);
    seedInput.addEventListener('keydown', (event) => {
        if (event.code === 'Enter') {
            handleGenerate();
        }
    });

})

async function handleGenerate() {
    if (generateLock) { return }

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
        generateLock = true;
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

function handleFetchError(error) {
    console.error(error);
    const responseElem = document.querySelector('#response-output');
    const loadingDotContainer = document.querySelector('#loading-dot-container');
    flashReponseBackground();
    loadingDotContainer.style.display = 'none';
    responseElem.innerText = 'There was an error making your request! Please try again later.';
}

function flashReponseBackground() {
    let backgroundFlashClass = 'response-background-flash';
    const responseElemContainer = document.querySelector('#response-output-container');
    responseElemContainer.classList.add(backgroundFlashClass);
    setTimeout(() => {
        responseElemContainer.classList.remove(backgroundFlashClass);
    }, flashRemovalTimeMilliseconds);
}

function typewriterEffect(element, text, delayMilliseconds = 5) {
    let i = 0;
    let responseSoFar = '';

    function typeChunk() {
        if (i < text.length) {
            element.innerHTML += text[i];
            responseSoFar += text[i];
            i++;
            if (i % 25 === 0 || i === text.length) {
                // Every n characters, re-render HTML to ensure tags and special characters appear properly
                element.innerHTML = responseSoFar;
            }
            setTimeout(typeChunk, delayMilliseconds);
        } else {
            generateLock = false;
        }
    }

    typeChunk();
}

