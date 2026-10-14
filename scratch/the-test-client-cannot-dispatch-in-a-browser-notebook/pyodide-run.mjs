import { loadPyodide } from "pyodide"; import fs from "fs";
const py = await loadPyodide(); await py.loadPackage(["micropip"], {messageCallback: () => {}});
py.FS.writeFile("/tmp/" + process.argv[2].split("/").pop(), fs.readFileSync(process.argv[2]));
await py.runPythonAsync(`import micropip; await micropip.install("emfs:/tmp/${process.argv[2].split("/").pop()}")`);
py.FS.mkdirTree("/home/pyodide/w"); py.FS.chdir("/home/pyodide/w");
try { py.runPython(fs.readFileSync(process.argv[3], "utf8")); } catch (e) { console.log("ERR3", String(e).slice(-400)); }
try { await py.runPythonAsync(fs.readFileSync(process.argv[4], "utf8")); } catch (e) { console.log("ERR4", String(e).slice(-600)); }
