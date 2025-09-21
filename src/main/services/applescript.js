const { exec } = require('child_process');
const { promisify } = require('util');
const path = require('path');
const fs = require('fs').promises;
const EventEmitter = require('events');

const execAsync = promisify(exec);

/**
 * AppleScript automation service for macOS system integration
 */
class AppleScriptService extends EventEmitter {
    constructor() {
        super();
        this.scriptsPath = path.join(__dirname, '../../automation');
        this.isInitialized = false;

        console.log('[AppleScript] Service initialized');
    }

    async initialize() {
        try {
            // Verify scripts directory exists
            await fs.access(this.scriptsPath);
            this.isInitialized = true;
            console.log('[AppleScript] Scripts directory verified:', this.scriptsPath);
            return true;
        } catch (error) {
            console.error('[AppleScript] Failed to initialize:', error);
            return false;
        }
    }

    /**
     * Execute raw AppleScript code
     */
    async executeScript(scriptCode) {
        if (!this.isInitialized) {
            throw new Error('AppleScript service not initialized');
        }

        try {
            console.log('[AppleScript] ========================================');
            console.log('[AppleScript] Executing script');
            console.log('[AppleScript] Script length:', scriptCode.length, 'characters');
            console.log('[AppleScript] First 200 chars:', scriptCode.substring(0, 200));
            console.log('[AppleScript] ========================================');

            // Write script to temp file for better handling of complex scripts
            const tempFile = path.join(__dirname, `temp_script_${Date.now()}.applescript`);
            await fs.writeFile(tempFile, scriptCode);

            console.log('[AppleScript] Script written to temp file:', tempFile);

            try {
                // Execute the script file
                const { stdout, stderr } = await execAsync(`osascript "${tempFile}" 2>&1`);

                // Clean up temp file
                await fs.unlink(tempFile).catch(err =>
                    console.warn('[AppleScript] Failed to delete temp file:', err)
                );

                if (stderr && !stderr.includes('NSReceiverEvaluationScriptError')) {
                    console.warn('[AppleScript] ⚠️ Script warning:', stderr);
                }

                if (stdout) {
                    console.log('[AppleScript] ✓ Script output:', stdout.trim());
                }

                console.log('[AppleScript] ✓ Script executed successfully');
                console.log('[AppleScript] ========================================');
                return { success: true, output: stdout.trim(), error: null };

            } catch (execError) {
                // Clean up temp file on error
                await fs.unlink(tempFile).catch(err =>
                    console.warn('[AppleScript] Failed to delete temp file:', err)
                );
                throw execError;
            }

        } catch (error) {
            console.error('[AppleScript] ✗ Script execution failed:', error.message);
            console.error('[AppleScript] Error code:', error.code);
            console.error('[AppleScript] Command stdout:', error.stdout);
            console.error('[AppleScript] Command stderr:', error.stderr);
            console.error('[AppleScript] Full error:', error);
            console.error('[AppleScript] ========================================');
            return { success: false, output: null, error: error.message };
        }
    }

    /**
     * Execute AppleScript from file
     */
    async executeScriptFile(filename, parameters = {}) {
        if (!this.isInitialized) {
            throw new Error('AppleScript service not initialized');
        }

        try {
            const scriptPath = path.join(this.scriptsPath, filename);
            console.log('[AppleScript] Loading script file:', scriptPath);

            // Read the script file
            let scriptContent = await fs.readFile(scriptPath, 'utf-8');

            // Replace parameters in the script (format: {{paramName}})
            for (const [key, value] of Object.entries(parameters)) {
                const placeholder = `{{${key}}}`;
                scriptContent = scriptContent.replace(new RegExp(placeholder, 'g'), value);
            }

            // Execute the script
            return await this.executeScript(scriptContent);
        } catch (error) {
            console.error('[AppleScript] Failed to execute script file:', error);
            return { success: false, output: null, error: error.message };
        }
    }

    /**
     * Create a calendar event
     */
    async createCalendarEvent(options) {
        const {
            title = 'New Event',
            startDate = new Date(),
            endDate = null,
            description = '',
            calendar = 'Work'
        } = options;

        console.log('[AppleScript-Calendar] ========================================');
        console.log('[AppleScript-Calendar] Creating event');
        console.log('[AppleScript-Calendar]   Title:', title);
        console.log('[AppleScript-Calendar]   Calendar:', calendar);
        console.log('[AppleScript-Calendar]   Start:', startDate.toLocaleString());
        console.log('[AppleScript-Calendar]   End:', endDate ? endDate.toLocaleString() : 'Auto (1 hour)');
        console.log('[AppleScript-Calendar]   Description:', description);
        console.log('[AppleScript-Calendar] ========================================');

        // Calculate end date if not provided (1 hour after start)
        const end = endDate || new Date(startDate.getTime() + 60 * 60 * 1000);

        console.log('[AppleScript-Calendar] Calculated end time:', end.toLocaleString());

        // Build the AppleScript - escape quotes in user input
        const escapedTitle = title.replace(/"/g, '\\"');
        const escapedDescription = description.replace(/"/g, '\\"');
        const escapedCalendar = calendar.replace(/"/g, '\\"');

        const script = `
            tell application "Calendar"
                activate
                delay 0.5

                -- Debug: Log available calendars
                set calNames to (name of calendars)
                log "Available calendars: " & (calNames as string)

                -- Check if calendar exists
                if calNames does not contain "${escapedCalendar}" then
                    log "Creating new calendar: ${escapedCalendar}"
                    make new calendar with properties {name:"${escapedCalendar}"}
                    delay 0.5
                else
                    log "Using existing calendar: ${escapedCalendar}"
                end if

                -- Get the target calendar
                set targetCal to calendar "${escapedCalendar}"

                -- Create the event
                log "Creating event: ${escapedTitle}"
                set newEvent to make new event at end of events of targetCal with properties {¬
                    summary:"${escapedTitle}", ¬
                    start date:date "${startDate.toLocaleString()}", ¬
                    end date:date "${end.toLocaleString()}", ¬
                    description:"${escapedDescription}"}

                log "Event created with ID: " & (id of newEvent as string)

                return "Event created successfully"
            end tell
        `;

        console.log('[AppleScript-Calendar] Executing script...');
        console.log('[AppleScript-Calendar] Script preview (first 500 chars):');
        console.log(script.substring(0, 500) + '...');

        const result = await this.executeScript(script);

        if (result.success) {
            console.log('[AppleScript-Calendar] ✓ Event created successfully');
            console.log('[AppleScript-Calendar]   Output:', result.output);
        } else {
            console.error('[AppleScript-Calendar] ✗ Failed to create event');
            console.error('[AppleScript-Calendar]   Error:', result.error);
        }

        console.log('[AppleScript-Calendar] ========================================');

        return result;
    }

    /**
     * Create a note
     */
    async createNote(options) {
        const {
            title = 'New Note',
            body = '',
            folder = 'Notes'
        } = options;

        console.log('[AppleScript-Notes] ========================================');
        console.log('[AppleScript-Notes] Creating note');
        console.log('[AppleScript-Notes]   Title:', title);
        console.log('[AppleScript-Notes]   Folder:', folder);
        console.log('[AppleScript-Notes]   Body length:', body.length, 'characters');
        console.log('[AppleScript-Notes]   Body preview:', body.substring(0, 100));
        console.log('[AppleScript-Notes] ========================================');

        // Escape quotes and newlines in user input
        const escapedTitle = title.replace(/"/g, '\\"').replace(/\n/g, '\\n');
        const escapedBody = body.replace(/"/g, '\\"').replace(/\n/g, '\\n');
        const escapedFolder = folder.replace(/"/g, '\\"');

        const script = `
            tell application "Notes"
                activate
                delay 0.5

                -- Debug: Log account info
                set accountCount to count of accounts
                log "Number of accounts: " & accountCount

                tell account 1
                    -- Debug: Log available folders
                    set folderNames to name of every folder
                    log "Available folders: " & (folderNames as string)

                    -- Check if folder exists
                    set folderExists to false
                    try
                        set targetFolder to folder "${escapedFolder}"
                        set folderExists to true
                        log "Using existing folder: ${escapedFolder}"
                    on error
                        log "Folder not found, using default Notes folder"
                        set targetFolder to folder "Notes"
                    end try

                    -- Create the note
                    log "Creating note: ${escapedTitle}"
                    set newNote to make new note at targetFolder with properties {¬
                        name:"${escapedTitle}", ¬
                        body:"${escapedBody}"}

                    log "Note created with ID: " & (id of newNote as string)

                    return "Note created successfully in folder: " & (name of targetFolder)
                end tell
            end tell
        `;

        console.log('[AppleScript-Notes] Executing script...');
        console.log('[AppleScript-Notes] Script preview (first 500 chars):');
        console.log(script.substring(0, 500) + '...');

        const result = await this.executeScript(script);

        if (result.success) {
            console.log('[AppleScript-Notes] ✓ Note created successfully');
            console.log('[AppleScript-Notes]   Output:', result.output);
        } else {
            console.error('[AppleScript-Notes] ✗ Failed to create note');
            console.error('[AppleScript-Notes]   Error:', result.error);
        }

        console.log('[AppleScript-Notes] ========================================');

        return result;
    }

    /**
     * Show system notification
     */
    async showNotification(title, message) {
        const script = `display notification "${message}" with title "${title}"`;
        return await this.executeScript(script);
    }

    /**
     * Get system information
     */
    async getSystemInfo() {
        const batteryScript = 'do shell script "pmset -g batt | grep -o \'[0-9]*%\'"';
        const battery = await this.executeScript(batteryScript);

        return {
            battery: battery.output
        };
    }
}

module.exports = AppleScriptService;