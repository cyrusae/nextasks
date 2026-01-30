# Problem Statement: Integrating Nextcloud Tasks into Bedroom Dashboard

## Context

I'm running Nextcloud on my homelab K3s cluster with CalDAV working successfully for calendar sync. I want to use Nextcloud Tasks for quick task entry ("I should do X today") and have those dated tasks appear on my bedroom dashboard alongside calendar events.

## Research Findings

### The Core Technical Issue

Nextcloud Tasks and Calendar share the same CalDAV backend, but they use different iCal component types:
- **Calendar Events**: `VEVENT` components
- **Tasks**: `VTODO` components

Nextcloud's web interface has a "show tasks in calendar" feature that displays both together, but this is a **UI-only overlay, not a data transformation**. When external applications query Nextcloud via CalDAV, they receive separate VEVENT and VTODO objects. Most calendar applications and dashboards only display VEVENT, silently ignoring VTODO.

### Why Standard Calendar Integrations Won't Work

- Most calendar widgets/integrations only query for VEVENT
- Tasks remain stored as VTODO regardless of having due dates
- The CalDAV endpoint at `/remote.php/dav/calendars/{username}/{calendar}/` contains both types, but clients must explicitly request VTODO components
- Third-party calendar dashboards (Magic Mirror, Home Assistant calendar cards, etc.) typically filter out VTODO

### Mobile Sync Status (FYI)

**Android**: Excellent support via DAVx⁵ + Tasks.org (CalDAV VTODO sync works well)

**iOS**: Broken since iOS 13 when Apple removed CalDAV support from native Reminders app. Third-party apps like BusyCal ($50) or 2Do (~$15) work but with limitations.

Official Nextcloud mobile apps (iOS/Android) are file-sync only and don't support Tasks at all.

## Opportunity

Since I'm building a custom dashboard with direct control over data queries, I can:

1. Query the Nextcloud CalDAV endpoint directly for both VEVENT and VTODO
2. Parse and display them together in chronological order
3. Style them distinctly (e.g., tasks with checkboxes, events without)
4. Filter/organize however makes sense for the bedroom display

## Technical Requirements

### CalDAV Endpoint

```
Base URL: https://nextcloud.dawnfire.casa/remote.php/dav/
Calendar URL: https://nextcloud.dawnfire.casa/remote.php/dav/calendars/{username}/{calendar-name}/
```

Already working for VEVENT sync; same endpoint contains VTODO data.

### Authentication

CalDAV uses HTTP Basic Auth with Nextcloud credentials. Since dashboard is on internal network, credentials can be securely stored in environment variables or config files.

### Query Approach

Most CalDAV libraries support filtering by component type:
- Request VEVENT for events
- Request VTODO for tasks
- Both can be filtered by date range

### Data Structure Differences

**VEVENT (Events)**:
- Has `DTSTART` (start time) and `DTEND` (end time)
- Can be all-day or timed
- Location, attendees, recurrence rules

**VTODO (Tasks)**:
- Has `DUE` (due date/time) - this is what makes them show on specific dates
- Has `STATUS` (NEEDS-ACTION, IN-PROCESS, COMPLETED, CANCELLED)
- Has `COMPLETED` date when finished
- Can have priority, percent-complete
- Can have parent/child relationships (subtasks)

### Display Considerations for Dashboard

**Visual distinction needed:**
- Tasks should show completion status (checkbox or checkmark)
- Events might show time duration, tasks show due time
- Overdue tasks might need special styling
- Completed tasks: hide entirely? Show struck through? Configurable?

**Chronological organization:**
- Tasks with `DUE` date sort by that date/time
- Tasks without `DUE` could go in separate "unscheduled" section or be omitted
- All-day events vs timed events vs timed tasks - sort order?

## Libraries & Tools

### Python
- `caldav` - mature, well-documented library
- `icalendar` - for parsing iCal data if needed
- Example: `pip install caldav`

### JavaScript/Node.js
- `tsdav` - modern, TypeScript-first
- `dav` - older but stable
- `ical.js` - Mozilla's iCal parser

### Direct HTTP
- Can use `curl` or similar to make REPORT requests to CalDAV endpoint
- More control but more manual parsing required

## Questions for Dashboard Implementation

1. **What's the dashboard built with?** (Framework, language, rendering approach)
2. **What timeframe to display?** (Today only? Next 7 days? Week view?)
3. **Completed tasks:** Hide, show struck through, or configurable?
4. **Overdue tasks:** Roll forward to "today" like Nextcloud does, or show on original date?
5. **Refresh frequency:** Real-time via WebSocket/SSE, periodic polling, manual refresh?
6. **Authentication storage:** Environment variables, config file, secrets manager?

## Success Criteria

- [ ] Dashboard queries Nextcloud CalDAV for both VEVENT and VTODO
- [ ] Tasks with due dates appear chronologically alongside events
- [ ] Visual distinction between tasks and events is clear
- [ ] Tasks can be marked complete (if interactive) or show completion status (if read-only)
- [ ] Performance is acceptable (CalDAV queries don't slow dashboard load significantly)

## References

- CalDAV RFC 4791: https://datatracker.ietf.org/doc/html/rfc4791
- iCalendar RFC 5545: https://datatracker.ietf.org/doc/html/rfc5545
- Nextcloud CalDAV docs: https://docs.nextcloud.com/server/latest/developer_manual/client_apis/CalDAV/
- Example VTODO structure: https://icalendar.org/iCalendar-RFC-5545/3-6-2-to-do-component.html

## Next Steps

1. Identify current dashboard technology stack
2. Choose appropriate CalDAV library for that stack
3. Prototype basic VTODO query and parsing
4. Design visual layout for mixed events/tasks
5. Implement full integration with error handling
6. Test with various task/event combinations