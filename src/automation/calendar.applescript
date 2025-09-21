-- Calendar automation for Clarity
-- Create and manage calendar events

on createEvent(eventTitle, eventStart, eventEnd, eventDescription, calendarName)
    tell application "Calendar"
        activate

        -- Check if calendar exists, create if needed
        set calNames to (name of calendars)
        if calNames does not contain calendarName then
            make new calendar with properties {name:calendarName}
        end if

        set targetCalendar to calendar calendarName

        -- Create the event
        make new event at end of events of targetCalendar with properties {¬
            summary:eventTitle, ¬
            start date:eventStart, ¬
            end date:eventEnd, ¬
            description:eventDescription}

        return "Event created: " & eventTitle
    end tell
end createEvent

on createQuickEvent(eventTitle, calendarName)
    -- Create a quick event starting now for 1 hour
    set startTime to (current date)
    set endTime to startTime + (1 * hours)

    return createEvent(eventTitle, startTime, endTime, "", calendarName)
end createQuickEvent

on createMeetingTomorrow(eventTitle, eventDescription, calendarName)
    -- Create a meeting for tomorrow at 10 AM
    set startTime to (current date) + (1 * days)
    set time of startTime to 10 * hours -- 10 AM
    set endTime to startTime + (1 * hours)

    return createEvent(eventTitle, startTime, endTime, eventDescription, calendarName)
end createMeetingTomorrow

on getUpcomingEvents(calendarName, daysAhead)
    tell application "Calendar"
        set targetCalendar to calendar calendarName
        set startDate to (current date)
        set endDate to startDate + (daysAhead * days)

        set eventList to {}
        set allEvents to events of targetCalendar

        repeat with anEvent in allEvents
            if start date of anEvent ≥ startDate and start date of anEvent ≤ endDate then
                set end of eventList to summary of anEvent & " - " & (start date of anEvent as string)
            end if
        end repeat

        return eventList
    end tell
end getUpcomingEvents