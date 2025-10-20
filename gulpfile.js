import gulp from 'gulp';
import through2 from 'through2';
import gettextParser from 'gettext-parser';
import fs from 'fs';
import path from 'path';
import chalk from 'chalk';
import { glob } from 'glob';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

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
 * Build task: Generate MO, L10N.php, and JSON files from all PO files
 */
async function build() {
    console.log(chalk.blue.bold('\n🔨 Building translation files...\n'));

    // Find all PO files
    const poFiles = await glob('**/*.po', {
        ignore: ['node_modules/**', '.git/**']
    });

    if (poFiles.length === 0) {
        console.log(chalk.yellow('⚠'), 'No PO files found');
        return Promise.resolve();
    }

    console.log(chalk.blue('ℹ'), `Found ${poFiles.length} PO file(s)\n`);

    // Process each PO file
    for (const poFile of poFiles) {
        const dir = path.dirname(poFile);
        const basename = path.basename(poFile, '.po');

        try {
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

    console.log(chalk.green.bold('\n✅ Build complete!\n'));
    return Promise.resolve();
}

/**
 * Watch task: Watch for PO file changes and rebuild
 */
function watch() {
    console.log(chalk.blue.bold('\n👀 Watching for changes...\n'));
    return gulp.watch(['plugins/**/*.po', 'themes/**/*.po'], build);
}

export { build, watch };
export default build;
