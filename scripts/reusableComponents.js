class OurHeader extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `
            <nav class="main-nav" aria-label="Main Navigation">
                <div class="navbar dark-mode">
                <a href="/#main">Home</a>
                <a href="/balticonomy/">Balticonomy</a>
                <a href="/#get-involved">Join Us</a>
                <a href="/newsletter/">Newsletter</a>
                </div>
            </nav>
        `
    }
}

class OurFooter extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `
            <footer id="footer">
                <ul class="copyright">
                    <li>&copy; Code Collective 2025</li>
                </ul>
            </footer>
        `
    }
}

class OurSocials extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `
            <aside id="socialButtons" class="social__container">
                <a
                    href="https://github.com/mdforward/fwdapp"
                    target="_blank"
                    class="social__link"
                >
                    <button class="social__button">
                        <img
                            src="/images/github_icon.png"
                            alt="GitHub icon"
                            class="social__icon"
                        />
                    </button>
                </a>
            </aside>
        `;
    }
}

class CalendarLegend extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `
            <aside class="calendar-legend" aria-label="Event category filters">
                <div class="legend-title">Filter by category:</div>
                <div class="legend-items" id="calendar-legend-items"></div>
            </aside>
            <button type="button" id="legend-visibility-toggle" class="legend-toggle-button" aria-expanded="true">
                Show legend
            </button>
        `;
    }
}

function addDonateShortcut() {
    const navs = document.querySelectorAll('.main-nav');

    navs.forEach((nav) => {
        if (nav.querySelector('.donate-shortcut')) {
            return;
        }

        const link = document.createElement('a');
        link.href = '/donate.html';
        link.className = 'donate-shortcut';
        link.setAttribute('aria-label', 'Donate');
        link.title = 'Donate';
        link.innerHTML = `
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                <path d="M12 21s-6.716-4.35-9.193-8.19C1.066 10.113 1.62 6.7 4.61 5.18c2.034-1.035 4.358-.33 5.74 1.346C11.733 4.85 14.057 4.145 16.09 5.18c2.99 1.52 3.544 4.933 1.803 7.63C18.716 16.65 12 21 12 21Z"></path>
            </svg>
        `;

        nav.appendChild(link);
    });
}

customElements.define('our-header', OurHeader)
customElements.define('our-footer', OurFooter)
customElements.define('our-slack-link', OurSocials)
customElements.define('calendar-legend', CalendarLegend)

document.addEventListener('DOMContentLoaded', addDonateShortcut);
