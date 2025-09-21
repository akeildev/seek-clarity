-- Notes automation for Clarity
-- Create and manage notes

on createNote(noteTitle, noteBody, folderName)
    tell application "Notes"
        activate

        -- Use the first account (iCloud)
        tell account 1
            -- Check if folder exists
            set folderExists to false
            try
                set targetFolder to folder folderName
                set folderExists to true
            on error
                -- Folder doesn't exist, use default Notes folder
                set targetFolder to folder "Notes"
            end try

            -- Create the note
            make new note at targetFolder with properties {¬
                name:noteTitle, ¬
                body:noteBody}

            return "Note created: " & noteTitle
        end tell
    end tell
end createNote

on createQuickNote(noteBody)
    -- Create a quick note with timestamp as title
    set noteTitle to "Quick Note - " & (current date as string)
    return createNote(noteTitle, noteBody, "Notes")
end createQuickNote

on createMeetingNotes(meetingTitle, attendees, topics, actionItems)
    -- Format meeting notes
    set lf to linefeed
    set noteBody to "Meeting: " & meetingTitle & lf & lf & ¬
        "Date: " & (current date as string) & lf & lf & ¬
        "Attendees:" & lf & attendees & lf & lf & ¬
        "Topics Discussed:" & lf & topics & lf & lf & ¬
        "Action Items:" & lf & actionItems

    return createNote("Meeting Notes - " & meetingTitle, noteBody, "Notes")
end createMeetingNotes

on createDailySummary(summary, keyPoints, tomorrow)
    -- Create daily summary note
    set lf to linefeed
    set noteTitle to "Daily Summary - " & (date string of (current date))

    set noteBody to "Daily Summary" & lf & lf & ¬
        "Date: " & (current date as string) & lf & lf & ¬
        "Summary:" & lf & summary & lf & lf & ¬
        "Key Points:" & lf & keyPoints & lf & lf & ¬
        "Tomorrow's Focus:" & lf & tomorrow

    return createNote(noteTitle, noteBody, "Notes")
end createDailySummary

on appendToNote(noteTitle, additionalText)
    tell application "Notes"
        tell account 1
            try
                -- Find note by title
                set targetNote to first note whose name contains noteTitle

                -- Append to existing body
                set body of targetNote to (body of targetNote) & linefeed & linefeed & additionalText

                return "Updated note: " & noteTitle
            on error
                return "Note not found: " & noteTitle
            end try
        end tell
    end tell
end appendToNote

on searchNotes(searchText)
    tell application "Notes"
        tell account 1
            set matchingNotes to {}

            -- Search through all notes
            set allNotes to every note

            repeat with aNote in allNotes
                if (name of aNote contains searchText) or (body of aNote contains searchText) then
                    set end of matchingNotes to name of aNote
                end if
            end repeat

            return matchingNotes
        end tell
    end tell
end searchNotes