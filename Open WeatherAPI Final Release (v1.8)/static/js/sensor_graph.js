document.addEventListener('DOMContentLoaded', function() {
    var burgerIcon = document.querySelector('.burger-icon');
    var menuOptions = document.querySelector('.menu-options');

    /**
     * Toggles the burger menu visibility by adding/removing the 'show-menu' and 'clicked' classes.
     */
    function toggleBurgerMenu() {
        menuOptions.classList.toggle('show-menu');
        burgerIcon.classList.toggle('clicked'); // Toggle the clicked class
    }

    /**
     * Event listener for the burger icon click to toggle the burger menu.
     * @param {Event} event - The click event object.
     */
    burgerIcon.addEventListener('click', function(event) {
        event.stopPropagation(); // Prevent event bubbling
        toggleBurgerMenu(); // Call the toggleBurgerMenu function
    });

    /**
     * Event listener for document clicks to close the burger menu if it's open.
     */
    document.addEventListener('click', function() {
        if (menuOptions.classList.contains('show-menu')) {
            toggleBurgerMenu(); // Close the menu if it's open
        }
    });

    /**
     * Event listener for clicks within the menu options to handle link interactions.
     * @param {Event} event - The click event object.
     */
    menuOptions.addEventListener('click', function(event) {
        event.stopPropagation(); // Prevent event bubbling

        // If the clicked element is a link within menu-options
        if (event.target.tagName === 'A') {
            // Get the href attribute of the clicked link
            var targetHref = event.target.getAttribute('href');

            // Close the burger menu
            toggleBurgerMenu();

            // If the target is login.html, prevent the default behavior and navigate to index.html
            if (targetHref === 'login.html') {
                event.preventDefault();
                window.location.href = 'index.html';
            }
        }
    });

    /**
     * Event listener for window scroll to close the burger menu if it's open when scrolling.
     */
    var lastScrollTop = 0;
    window.addEventListener('scroll', function() {
        var st = window.pageYOffset || document.documentElement.scrollTop;

        // If user scrolls up or down and menu is open, close it
        if (st > lastScrollTop && menuOptions.classList.contains('show-menu')) {
            toggleBurgerMenu();
        } else if (st < lastScrollTop && menuOptions.classList.contains('show-menu')) {
            toggleBurgerMenu();
        }
        lastScrollTop = st <= 0 ? 0 : st; // For mobile or negative scrolling
    });

    /**
     * Prevents the user from navigating back using the browser's back button.
     */
    history.pushState(null, null, location.href);
    window.onpopstate = function(event) {
        history.go(1);
    };
});
