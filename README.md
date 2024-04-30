# abcvoting-app
An online app for computing approval based committee election rules. Available at [https://pref.tools/abcvoting/](https://pref.tools/abcvoting/).

The app is based on the [`abcvoting`](https://github.com/martinlackner/abcvoting) python package developed by Martin Lackner and others. It is run in the browser using [`pyodide`](https://pyodide.org/en/stable/) (a Python interpreter compiled in WebAssembly). ILPs are solved using the [HiGHS](https://highs.dev/) solver, run in the browser using the [`highs-js`](https://github.com/lovasoa/highs-js) WebAssembly compilation.

<img width="750" alt="screenshot" src="https://github.com/DominikPeters/abcvoting-app/assets/3543224/c85706a8-16e3-4bc6-b0cd-334cb92ff39a">

## Overview

The ABC Voting app is built using the following technologies:

- `abcvoting`: A Python package developed by Martin Lackner and others for computing approval-based committee election rules.
- `pyodide`: A Python interpreter compiled in WebAssembly, used to run Python code in the browser.
- `HiGHS`: A solver for integer linear programming (ILP) problems, compiled to WebAssembly: `highs-js`.

The app allows users to input approval-based voting profiles, compute committee election rules, generate random profiles, and explore the axiomatic properties and algorithms used to find the selected committees.

## Repository Structure

The repository is structured as follows:

- `index.html`: The main HTML file that serves as the entry point for the app.
- `js/`: Contains the JavaScript modules that make up the app's functionality.
  - `abcvoting.js`: The main module that orchestrates the app's functionality.
  - `globalState.js`: Manages the global state of the app (current profile etc.).
  - `InstanceManagement.js`: Provides functions for managing the voting profile.
  - `CalculateRules.js`: Handles the computation of committee election rules.
  - `TableBuilder.js`: Builds the table for displaying voting profiles and results.
  - `SettingsManagement.js`: Manages app settings.
  - `constants.js`: Defines constants used throughout the app (e. g., names of voting rules).
  - `ExportModal.js`: Implements the export functionality for saving voting profiles.
  - `FileDrop.js`: Handles drag-and-drop functionality for importing voting profiles.
  - `LibraryModal.js`: Implements the library modal for selecting pre-defined voting profiles.
  - `loadPython.js`: Loads the Python interpreter and required packages.
  - `logger.js`: Provides logging functionality.
  - `Randomizer.js`: Generates random voting profiles.
  - `RuleSelection.js`: Handles the user selection of which committee election rules to display.
  - `clipboard.js`: Provides functionality for copying and pasting voting profiles.
  - `URL.js`: Handles URL-related functionality.
  - `utils.js`: Contains utility functions used throughout the app.
- `imports/`: Contains external libraries and dependencies.
  - `highs.js`: The HiGHS solver compiled to WebAssembly.
  - `hystmodal.min.js`: A library for creating modal dialogs.

## Usage

To use the ABC Voting app, simply open `index.html` in a web browser (served via a web server which can be started with `python -m http.server`, for example).
The app will load the necessary dependencies and provide an interface for inputting voting profiles, computing committee election rules, and exploring the results.

Users can input voting profiles manually, import profiles from files, or generate random profiles. The app computes the selected committees using various approval-based committee election rules and displays the results in a table. Users can click on a selected committee to view its axiomatic properties and the algorithm used to find it.

## Dependencies

The app relies on the following external dependencies:

- `pyodide`: A Python interpreter compiled to WebAssembly.
- `HiGHS`: A solver for integer linear programming problems.
- `hystmodal`: A library for creating modal dialogs.
- `popper.js`: A library for positioning tooltips and popovers.
- `tippy.js`: A library for creating tooltips.

These dependencies are loaded via CDN links in the `index.html` file.

## Contributing

Contributions to the ABC Voting app are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the GitHub repository.

## License

The ABC Voting app is open-source software licensed under the [MIT License](LICENSE).