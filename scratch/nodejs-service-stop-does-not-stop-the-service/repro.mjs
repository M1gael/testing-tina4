// Reproduction: ServiceRunner.stop() does not stop a class-based Tina4Service.
//
// Two services are registered the two ways the framework documents:
//   - "class_service"  via ServiceRunner.registerService(name, new Tina4Service subclass)
//   - "plain_service"  via ServiceRunner.register(name, async (ctx) => ...)
// Both loop until told to stop, each using the exit condition its own pattern
// documents: this.shouldStop() for the class, ctx.running for the callable.
//
// Exit code 0 = both stopped (fixed).  Exit code 1 = class service still running (defect).

import { ServiceRunner, Tina4Service } from "tina4-nodejs";
import { readFileSync } from "node:fs";

const version = JSON.parse(
  readFileSync(new URL("./node_modules/tina4-nodejs/package.json", import.meta.url), "utf8"),
).version;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class CountingService extends Tina4Service {
  constructor() {
    super();
    this.count = 0;
    this.exited = false;
  }
  // Exactly the loop the Tina4Service docstring shows (service.ts:199-209).
  async run() {
    while (!this.shouldStop()) {
      this.count += 1;
      await sleep(5);
    }
    this.exited = true;
  }
}

const classService = new CountingService();
let plainCount = 0;
let plainExited = false;

ServiceRunner.registerService("class_service", classService);
ServiceRunner.register(
  "plain_service",
  async (ctx) => {
    while (ctx.running) {
      plainCount += 1;
      await sleep(5);
    }
    plainExited = true;
  },
  { daemon: true },
);

ServiceRunner.start();
await sleep(300);

const classAtStop = classService.count;
const plainAtStop = plainCount;

const t0 = process.hrtime.bigint();
ServiceRunner.stop();
const stopMs = Number(process.hrtime.bigint() - t0) / 1e6;

await sleep(300);

const classDelta = classService.count - classAtStop;
const plainDelta = plainCount - plainAtStop;

console.log(`tina4-nodejs ${version}  (released, from npm)`);
console.log(`stop() returned in ${stopMs.toFixed(4)} ms`);
console.log("");
console.log("service        loops at stop()   loops 300ms later   delta   run() exited   isRunning()");
console.log(
  `class_service  ${String(classAtStop).padStart(15)}   ${String(classService.count).padStart(17)}   ${String(classDelta).padStart(5)}   ${String(classService.exited).padStart(12)}   ${ServiceRunner.isRunning("class_service")}`,
);
console.log(
  `plain_service  ${String(plainAtStop).padStart(15)}   ${String(plainCount).padStart(17)}   ${String(plainDelta).padStart(5)}   ${String(plainExited).padStart(12)}   ${ServiceRunner.isRunning("plain_service")}`,
);
console.log("");

const ok = classDelta === 0 && classService.exited === true;
if (ok) {
  console.log("PASS  stop() stopped the class-based service.");
} else {
  console.log(`FAIL  stop() did not stop the class-based service:`);
  console.log(`      it ran ${classDelta} more loops after stop() returned, and run() has not exited.`);
  console.log(`      The plain-callable control stopped correctly (delta ${plainDelta}), so the`);
  console.log(`      ctx.running path works; only the class-based path is broken.`);
}

classService.stop();          // stop it by hand so the process can exit
await sleep(20);
process.exit(ok ? 0 : 1);
