'use strict';

const index = require('./shared/ni.bde039bb.cjs');
require('node:fs');
require('node:path');
require('node:process');
require('node:buffer');
require('node:child_process');
require('child_process');
require('path');
require('fs');
require('node:url');
require('node:os');
require('node:timers/promises');
require('stream');
require('node:util');
require('os');
require('tty');
require('readline');
require('events');
require('fs/promises');

index.runCli(
  (agent, _, hasLock) => index.parseNi(agent, ["--frozen-if-present"], hasLock),
  { autoInstall: true }
);
