import gulp from 'gulp';
import through2 from 'through2';
import gettextParser from 'gettext-parser';
import fs from 'fs';
import path from 'path';
import chalk from 'chalk';
import { glob } from 'glob';
import { exec } from 'child_process';
import { promisify } from 'util';
import crypto from 'crypto';

const execAsync = promisify(exec);

/**
 * Load blocked strings from blocked-strings.json
 * @returns {Array} - Array of blocked msgid patterns
 */
function loadBlockedStrings() {
    try {
        const blockedStringsPath = path.join(process.cwd(), 'blocked-strings.json');
        if (!fs.existsSync(blockedStringsPath)) {
            return [];
        }
        const data = JSON.parse(fs.readFileSync(blockedStringsPath, 'utf-8'));
        // Reconstruct the strings from dot-separated characters
        return data.blocked_patterns.map(p => p.msgid_parts.split('.').join(''));
    } catch (err) {
        console.log(chalk.yellow('⚠'), 'Could not load blocked strings:', err.message);
        return [];
    }
}

/**
 * Remove blocked strings from PO file
 * @param {string} poFile - Path to the PO file
 * @returns {boolean} - True if any strings were removed
 */
function removeBlockedStrings(poFile) {
    try {
        const blockedStrings = loadBlockedStrings();
        if (blockedStrings.length === 0) {
            return false;
        }

        const poContent = fs.readFileSync(poFile, 'utf-8');
        const po = gettextParser.po.parse(poContent);
        const translations = po.translations[''] || {};

        let removedCount = 0;
        for (const blockedMsgid of blockedStrings) {
            if (translations[blockedMsgid]) {
                delete translations[blockedMsgid];
                removedCount++;
            }
        }

        if (removedCount > 0) {
            // Write back the cleaned PO file
            const cleanedPo = gettextParser.po.compile(po);
            fs.writeFileSync(poFile, cleanedPo);
            console.log(chalk.yellow('🔒'), `Removed ${removedCount} blocked string(s) from:`, chalk.cyan(poFile));
            return true;
        }

        return false;
    } catch (err) {
        console.log(chalk.yellow('⚠'), 'Error removing blocked strings:', err.message);
        return false;
    }
}

/**
 * Check if PO file has changed compared to the last committed version
 * @param {string} poFile - Path to the PO file
 * @returns {Promise<boolean>} - True if file changed, false otherwise
 */
async function hasPoFileChanged(poFile) {
    try {
        // Get the file content from git HEAD
        const { stdout: gitContent } = await execAsync(`git show HEAD:"${poFile}" 2>/dev/null`);

        // Read current file content
        const currentContent = fs.readFileSync(poFile, 'utf-8');

        // Parse both versions
        const gitPo = gettextParser.po.parse(gitContent);
        const currentPo = gettextParser.po.parse(currentContent);

        // Compare translations (excluding headers like PO-Revision-Date)
        const gitTranslations = JSON.stringify(gitPo.translations);
        const currentTranslations = JSON.stringify(currentPo.translations);

        return gitTranslations !== currentTranslations;
    } catch (err) {
        // File doesn't exist in git (new file) or other error
        return true;
    }
}

/**
 * Update PO-Revision-Date header in PO file if translations changed
 * @param {string} poFile - Path to the PO file
 */
async function updateRevisionDate(poFile) {
    try {
        const hasChanged = await hasPoFileChanged(poFile);

        if (!hasChanged) {
            return false;
        }

        // Read and parse PO file
        const poContent = fs.readFileSync(poFile, 'utf-8');
        const now = new Date();

        // Format date as: YYYY-MM-DD HH:MM+ZZZZ
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const tzOffset = -now.getTimezoneOffset();
        const tzHours = String(Math.floor(Math.abs(tzOffset) / 60)).padStart(2, '0');
        const tzMinutes = String(Math.abs(tzOffset) % 60).padStart(2, '0');
        const tzSign = tzOffset >= 0 ? '+' : '-';

        const revisionDate = `${year}-${month}-${day} ${hours}:${minutes}${tzSign}${tzHours}${tzMinutes}`;

        // Update PO-Revision-Date in the file
        const updatedContent = poContent.replace(
            /"PO-Revision-Date:.*?\\n"/,
            `"PO-Revision-Date: ${revisionDate}\\n"`
        );

        if (updatedContent !== poContent) {
            fs.writeFileSync(poFile, updatedContent);
            console.log(chalk.blue('ℹ'), 'Updated PO-Revision-Date:', chalk.cyan(poFile));
            return true;
        }

        return false;
    } catch (err) {
        console.log(chalk.yellow('⚠'), 'Could not update revision date:', err.message);
        return false;
    }
}

/**
 * Convert PO file to MO (binary format)
 */
function po2mo() {
    return through2.obj(function (file, enc, cb) {
        if (file.isNull()) {
            return cb(null, file);
        }

        if (file.isStream()) {
            this.emit('error', new Error('Streams not supported!'));
            return cb();
        }

        try {
            // Parse PO file
            const po = gettextParser.po.parse(file.contents);

            // Convert to MO
            const mo = gettextParser.mo.compile(po);

            // Update file contents and extension
            file.contents = mo;
            file.extname = '.mo';

            console.log(chalk.green('✓'), 'Generated MO:', chalk.cyan(file.relative));

            cb(null, file);
        } catch (err) {
            console.log(chalk.red('✗'), 'Error processing:', file.relative, err.message);
            cb();
        }
    });
}

/**
 * Convert PO file to L10N.php (WordPress 6.5+ optimized format)
 */
function po2php() {
    return through2.obj(function (file, enc, cb) {
        if (file.isNull()) {
            return cb(null, file);
        }

        if (file.isStream()) {
            this.emit('error', new Error('Streams not supported!'));
            return cb();
        }

        try {
            // Parse PO file
            const po = gettextParser.po.parse(file.contents);
            const translations = po.translations[''] || {};
            const headers = po.headers || {};

            // Build messages array
            const messages = {};
            for (const [msgid, data] of Object.entries(translations)) {
                if (msgid === '') continue;
                const msgstr = data.msgstr[0];
                if (!msgstr) continue;
                messages[msgid] = msgstr;
            }

            // Build PHP content with WordPress 6.5+ format
            let phpContent = '<?php\n';
            phpContent += 'return [';

            // Add metadata from PO headers
            if (headers['Project-Id-Version']) {
                phpContent += `\n\t'project-id-version' => '${headers['Project-Id-Version']}',`;
            }
            if (headers['Report-Msgid-Bugs-To']) {
                phpContent += `\n\t'report-msgid-bugs-to' => '${headers['Report-Msgid-Bugs-To']}',`;
            }
            if (headers['POT-Creation-Date']) {
                phpContent += `\n\t'pot-creation-date' => '${headers['POT-Creation-Date']}',`;
            }
            if (headers['PO-Revision-Date']) {
                phpContent += `\n\t'po-revision-date' => '${headers['PO-Revision-Date']}',`;
            }
            if (headers['Last-Translator']) {
                phpContent += `\n\t'last-translator' => '${headers['Last-Translator']}',`;
            }
            if (headers['Language-Team']) {
                phpContent += `\n\t'language-team' => '${headers['Language-Team']}',`;
            }
            if (headers.Language || headers.language) {
                const lang = headers.Language || headers.language;
                // Extract language code only (e.g., 'hu_HU' -> 'hu')
                const langCode = lang.split('_')[0];
                phpContent += `\n\t'language' => '${langCode}',`;
            }
            if (headers['MIME-Version']) {
                phpContent += `\n\t'mime-version' => '${headers['MIME-Version']}',`;
            }
            if (headers['Content-Type']) {
                phpContent += `\n\t'content-type' => '${headers['Content-Type']}',`;
            }
            if (headers['Content-Transfer-Encoding']) {
                phpContent += `\n\t'content-transfer-encoding' => '${headers['Content-Transfer-Encoding']}',`;
            }
            if (headers['Plural-Forms']) {
                phpContent += `\n\t'plural-forms' => '${headers['Plural-Forms']}',`;
            }
            if (headers['X-Generator']) {
                phpContent += `\n\t'x-generator' => '${headers['X-Generator']}',`;
            }
            if (headers['X-Plugin-Name']) {
                phpContent += `\n\t'x-plugin-name' => '${headers['X-Plugin-Name']}',`;
            }
            if (headers['X-Plugin-Version']) {
                phpContent += `\n\t'x-plugin-version' => '${headers['X-Plugin-Version']}',`;
            }

            // Add messages array
            phpContent += '\n\t\'messages\' => [';

            for (const [msgid, msgstr] of Object.entries(messages)) {
                const escapedMsgid = msgid.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n');
                const escapedMsgstr = msgstr.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n');
                phpContent += `\n\t\t'${escapedMsgid}' => '${escapedMsgstr}',`;
            }

            phpContent += '\n\t],';
            phpContent += '\n];\n';

            // Update file contents and extension
            file.contents = Buffer.from(phpContent);
            file.extname = '.l10n.php';

            console.log(chalk.green('✓'), 'Generated PHP:', chalk.cyan(file.relative));

            cb(null, file);
        } catch (err) {
            console.log(chalk.red('✗'), 'Error processing:', file.relative, err.message);
            cb();
        }
    });
}

/**
 * Generate JSON translation files for JavaScript using WP-CLI
 */
async function generateJsonTranslations(poFile) {
    const dir = path.dirname(poFile);
    const basename = path.basename(poFile, '.po');

    try {
        // Check if wp-cli is available
        await execAsync('wp --version');

        // Generate JSON files using WP-CLI
        // The command will create JSON files for all JavaScript handles found in the PO file
        const { stderr } = await execAsync(`wp i18n make-json "${poFile}" "${dir}" --no-purge`, {
            cwd: process.cwd()
        });

        if (stderr && !stderr.includes('Success')) {
            console.log(chalk.yellow('⚠'), 'JSON generation warning:', stderr);
        }

        // Count generated JSON files
        const jsonFiles = await glob(path.join(dir, `${basename}-*.json`));

        if (jsonFiles.length > 0) {
            console.log(chalk.green('✓'), `Generated ${jsonFiles.length} JSON file(s) for:`, chalk.cyan(basename));
            jsonFiles.forEach(jsonFile => {
                console.log(chalk.gray('  →'), path.basename(jsonFile));
            });
        }

        return true;
    } catch (err) {
        if (err.message.includes('wp: command not found') || err.message.includes('\'wp\' is not recognized')) {
            console.log(chalk.yellow('⚠'), 'WP-CLI not found. Skipping JSON generation.');
            console.log(chalk.gray('  Install WP-CLI to enable JSON translations: https://wp-cli.org'));
            return false;
        }
        console.log(chalk.yellow('⚠'), 'Could not generate JSON for:', poFile);
        console.log(chalk.gray('  Error:'), err.message);
        return false;
    }
}

/**
 * Calculate hash of translation content (excluding metadata that changes frequently)
 * @param {object} po - Parsed PO object
 * @returns {string} - Hash of translation content
 */
function getTranslationHash(po) {
    const translations = po.translations[''] || {};

    // Create a deterministic string of translations only (no metadata)
    const translationPairs = [];
    for (const [msgid, data] of Object.entries(translations)) {
        if (msgid === '') continue; // Skip header
        const msgstr = data.msgstr[0];
        if (!msgstr) continue;
        translationPairs.push(`${msgid}::${msgstr}`);
    }

    // Sort to ensure consistent hash
    translationPairs.sort();
    const content = translationPairs.join('|');

    // Create hash
    return crypto.createHash('md5').update(content).digest('hex');
}

/**
 * Check if PO file translations changed (ignoring metadata)
 * @param {string} poFile - Path to PO file
 * @param {string} hashFile - Path to hash cache file
 * @returns {boolean} - True if translations changed
 */
function hasTranslationsChanged(poFile, hashFile) {
    try {
        const poContent = fs.readFileSync(poFile);
        const po = gettextParser.po.parse(poContent);
        const currentHash = getTranslationHash(po);

        // Check if hash file exists
        if (!fs.existsSync(hashFile)) {
            // No hash file, consider it changed
            fs.writeFileSync(hashFile, currentHash);
            return true;
        }

        const previousHash = fs.readFileSync(hashFile, 'utf-8').trim();

        if (currentHash !== previousHash) {
            // Hash changed, update it
            fs.writeFileSync(hashFile, currentHash);
            return true;
        }

        return false;
    } catch (err) {
        // On error, assume changed
        return true;
    }
}

/**
 * Build task: Generate MO, L10N.php, and JSON files from all PO files
 */
async function build() {
    console.log(chalk.blue.bold('\n🔨 Building translation files...\n'));

    // Find all PO files in formal and informal directories
    const poFiles = await glob('{formal,informal}/**/*.po', {
        ignore: ['node_modules/**', '.git/**']
    });

    if (poFiles.length === 0) {
        console.log(chalk.yellow('⚠'), 'No PO files found');
        return Promise.resolve();
    }

    console.log(chalk.blue('ℹ'), `Found ${poFiles.length} PO file(s)\n`);

    // Track updated and skipped files
    const updatedFiles = [];
    const skippedFiles = [];

    // Process each PO file
    for (const poFile of poFiles) {
        const dir = path.dirname(poFile);
        const basename = path.basename(poFile, '.po');
        const hashFile = path.join(dir, `.${basename}.hash`);

        try {
            // Remove blocked strings (API key placeholders, etc.)
            removeBlockedStrings(poFile);

            // Check if translations actually changed
            const translationsChanged = hasTranslationsChanged(poFile, hashFile);

            if (!translationsChanged) {
                skippedFiles.push(poFile);
                console.log(chalk.gray('⊘'), 'Skipped (no changes):', chalk.gray(poFile));
                continue;
            }

            // Update PO-Revision-Date if translations changed
            const wasUpdated = await updateRevisionDate(poFile);
            if (wasUpdated) {
                updatedFiles.push(poFile);
            }

            const poContent = fs.readFileSync(poFile);

            // Generate MO file
            const po = gettextParser.po.parse(poContent);
            const mo = gettextParser.mo.compile(po);
            const moPath = path.join(dir, `${basename}.mo`);
            fs.writeFileSync(moPath, mo);
            console.log(chalk.green('✓'), 'Generated MO:', chalk.cyan(moPath));

            // Generate L10N.php file (WordPress 6.5+ format)
            const translations = po.translations[''] || {};
            const headers = po.headers || {};

            // Build messages array
            const messages = {};
            for (const [msgid, data] of Object.entries(translations)) {
                if (msgid === '') continue;
                const msgstr = data.msgstr[0];
                if (!msgstr) continue;
                messages[msgid] = msgstr;
            }

            // Build PHP content with WordPress 6.5+ format
            let phpContent = '<?php\n';
            phpContent += 'return [';

            // Add metadata from PO headers
            if (headers['Project-Id-Version']) {
                phpContent += `\n\t'project-id-version' => '${headers['Project-Id-Version']}',`;
            }
            if (headers['Report-Msgid-Bugs-To']) {
                phpContent += `\n\t'report-msgid-bugs-to' => '${headers['Report-Msgid-Bugs-To']}',`;
            }
            if (headers['POT-Creation-Date']) {
                phpContent += `\n\t'pot-creation-date' => '${headers['POT-Creation-Date']}',`;
            }
            if (headers['PO-Revision-Date']) {
                phpContent += `\n\t'po-revision-date' => '${headers['PO-Revision-Date']}',`;
            }
            if (headers['Last-Translator']) {
                phpContent += `\n\t'last-translator' => '${headers['Last-Translator']}',`;
            }
            if (headers['Language-Team']) {
                phpContent += `\n\t'language-team' => '${headers['Language-Team']}',`;
            }
            if (headers.Language || headers.language) {
                const lang = headers.Language || headers.language;
                // Extract language code only (e.g., 'hu_HU' -> 'hu')
                const langCode = lang.split('_')[0];
                phpContent += `\n\t'language' => '${langCode}',`;
            }
            if (headers['MIME-Version']) {
                phpContent += `\n\t'mime-version' => '${headers['MIME-Version']}',`;
            }
            if (headers['Content-Type']) {
                phpContent += `\n\t'content-type' => '${headers['Content-Type']}',`;
            }
            if (headers['Content-Transfer-Encoding']) {
                phpContent += `\n\t'content-transfer-encoding' => '${headers['Content-Transfer-Encoding']}',`;
            }
            if (headers['Plural-Forms']) {
                phpContent += `\n\t'plural-forms' => '${headers['Plural-Forms']}',`;
            }
            if (headers['X-Generator']) {
                phpContent += `\n\t'x-generator' => '${headers['X-Generator']}',`;
            }
            if (headers['X-Plugin-Name']) {
                phpContent += `\n\t'x-plugin-name' => '${headers['X-Plugin-Name']}',`;
            }
            if (headers['X-Plugin-Version']) {
                phpContent += `\n\t'x-plugin-version' => '${headers['X-Plugin-Version']}',`;
            }

            // Add messages array
            phpContent += '\n\t\'messages\' => [';

            for (const [msgid, msgstr] of Object.entries(messages)) {
                const escapedMsgid = msgid.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n');
                const escapedMsgstr = msgstr.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\n/g, '\\n');
                phpContent += `\n\t\t'${escapedMsgid}' => '${escapedMsgstr}',`;
            }

            phpContent += '\n\t],';
            phpContent += '\n];\n';

            const phpPath = path.join(dir, `${basename}.l10n.php`);
            fs.writeFileSync(phpPath, phpContent);
            console.log(chalk.green('✓'), 'Generated PHP:', chalk.cyan(phpPath));

            // Generate JSON files for JavaScript translations
            await generateJsonTranslations(poFile);

        } catch (err) {
            console.log(chalk.red('✗'), 'Error processing:', poFile, err.message);
        }
    }

    // Display summary
    console.log(chalk.blue.bold('\n📊 Build Summary:\n'));

    if (updatedFiles.length > 0) {
        console.log(chalk.green('  ✓'), `Generated: ${updatedFiles.length} file(s)`);
    }

    if (skippedFiles.length > 0) {
        console.log(chalk.gray('  ⊘'), `Skipped (unchanged): ${skippedFiles.length} file(s)`);
    }

    const processedCount = updatedFiles.length + skippedFiles.length;
    console.log(chalk.blue('\n  Total processed:'), processedCount, 'file(s)');

    if (updatedFiles.length > 0) {
        console.log(chalk.green.bold('\n✅ Build complete!\n'));
    } else {
        console.log(chalk.gray.bold('\n✅ Build complete (no changes detected)\n'));
    }

    return Promise.resolve();
}

/**
 * Watch task: Watch for PO file changes and rebuild
 */
function watch() {
    console.log(chalk.blue.bold('\n👀 Watching for changes...\n'));
    return gulp.watch(['formal/**/*.po', 'informal/**/*.po'], build);
}

export { build, watch };
export default build;
