/*
Copyright (C) 2025 AIDC-AI
This project is licensed under the MIT License (SPDX-License-identifier: MIT).
*/
function initMessage() {
    // Timing configuration
    const TIMING_CONFIG = {
        PAGE_LOAD_DELAY: 150,        // Page load delay (ms) - Ensure DOM stable and React rendering completed
        BUTTON_CHECK_INTERVAL: 100,  // Button check interval (ms) - Starter button detection frequency
        BASIC_ELEMENT_CHECK_INTERVAL: 200,  // Basic element check interval (ms) - Page initialization detection frequency
        MAX_RETRY_COUNT: 50,         // Maximum retry count - Avoid infinite loop
    };

    // Get URL parameters
    function getUrlParam(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    }

    // Check and automatically trigger the starter in the URL parameters
    function checkAndTriggerUrlStarter() {
        const starterId = getUrlParam('starter');
        if (starterId) {
            // Process URL encoding and space conversion
            const decodedStarterId = decodeURIComponent(starterId);
            const normalizedStarterId = decodedStarterId.replace(/\s+/g, '-'); // Replace spaces with hyphens
            const targetElementId = `starter-${normalizedStarterId}`;

            // Wait for the starter button to be ready
            let retryCount = 0;
            const waitForStarterAndTrigger = () => {
                if (retryCount >= TIMING_CONFIG.MAX_RETRY_COUNT) {
                    return;
                }

                const starterButton = document.getElementById(targetElementId);
                if (starterButton) {
                    // Check if the button is really available
                    const isButtonReady = starterButton.offsetParent !== null && // Element visible
                                         !starterButton.disabled &&              // Not disabled
                                         starterButton.style.display !== 'none'; // Not hidden

                    if (isButtonReady) {
                        // Slightly delay to ensure the page is fully loaded and React rendering completed
                        setTimeout(() => {
                            try {
                                // Confirm again that the button still exists and is available
                                const buttonCheck = document.getElementById(targetElementId);
                                if (buttonCheck && !buttonCheck.disabled) {
                                    buttonCheck.click();
                                }
                            } catch (error) {
                            }
                        }, TIMING_CONFIG.PAGE_LOAD_DELAY);
                    } else {
                        retryCount++;
                        setTimeout(waitForStarterAndTrigger, TIMING_CONFIG.BUTTON_CHECK_INTERVAL);
                    }
                } else {
                    // If the starter button is not ready, continue waiting
                    retryCount++;
                    setTimeout(waitForStarterAndTrigger, TIMING_CONFIG.BUTTON_CHECK_INTERVAL);
                }
            };

            waitForStarterAndTrigger();
        }
    }

    // Initialize
    function init() {
        const checkReady = () => {
            // Wait for the page basic elements and React application to load completed
            const isPageReady = document.body && 
                               document.getElementById('starters') && // Starter container exists
                               document.querySelectorAll('[id^="starter-"]').length > 0; // At least one starter button                                                                                                       
            
            if (isPageReady) {
                // Check URL parameters and automatically trigger the starter
                checkAndTriggerUrlStarter();
            } else {
                setTimeout(checkReady, TIMING_CONFIG.BASIC_ELEMENT_CHECK_INTERVAL);
            }
        };
        checkReady();
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}

initMessage();