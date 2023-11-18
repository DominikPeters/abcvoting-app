# abcvoting-app
An online app for computing approval based committee election rules. Available at [https://pref.tools/abcvoting/](https://pref.tools/abcvoting/).

The app is based on the [`abcvoting`](https://github.com/martinlackner/abcvoting) python package developed by Martin Lackner and others. It is run in the browser using [`pyodide`](https://pyodide.org/en/stable/) (a Python interpreter compiled in WebAssembly). ILPs are solved using the [HiGHS](https://highs.dev/) solver, run in the browser using the [`highs-js`](https://github.com/lovasoa/highs-js) WebAssembly compilation.

<img width="750" alt="screenshot" src="https://github.com/DominikPeters/abcvoting-app/assets/3543224/c85706a8-16e3-4bc6-b0cd-334cb92ff39a">
