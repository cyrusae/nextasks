"""
CalDAV client for interacting with Nextcloud Tasks.

Handles VTODO creation, retrieval, and completion via CalDAV protocol.
"""

import logging
from datetime import datetime, date
from typing import List, Optional
from dataclasses import dataclass

import caldav
from caldav import DAVClient
from icalendar import Calendar, Todo

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Represents a task from Nextcloud."""
    uid: str
    title: str
    due: Optional[datetime]
    completed: bool
    completed_date: Optional[datetime] = None
    description: Optional[str] = None
    priority: int = 0
    
    def __str__(self):
        status = "✅" if self.completed else "📝"
        due_str = f" (due {self.due.strftime('%Y-%m-%d %H:%M')})" if self.due else ""
        return f"{status} {self.title}{due_str}"


class NextcloudTasksClient:
    """Client for managing tasks in Nextcloud via CalDAV."""
    
    def __init__(self, url: str, username: str, password: str):
        """
        Initialize Nextcloud Tasks client.
        
        Args:
            url: Nextcloud base URL (e.g., https://nextcloud.dawnfire.casa)
            username: Nextcloud username
            password: Nextcloud app password
        """
        self.url = url
        self.username = username
        
        # Build CalDAV URL
        caldav_url = f"{url}/remote.php/dav"
        
        logger.info(f"Initializing CalDAV client for {caldav_url}")
        
        # Create DAV client
        self.client = DAVClient(
            url=caldav_url,
            username=username,
            password=password
        )
        
        # Will be set on first connection
        self._calendar = None
        
    def test_connection(self) -> bool:
        """
        Test connection to Nextcloud.
        
        Returns:
            True if connection successful
            
        Raises:
            Exception if connection fails
        """
        logger.info("Testing Nextcloud connection...")
        
        try:
            principal = self.client.principal()
            calendars = principal.calendars()
            
            logger.info(f"✅ Connected! Found {len(calendars)} calendar(s)")
            
            # Find first calendar that supports tasks (has VTODO)
            for cal in calendars:
                # Try to get calendar properties
                try:
                    # Check if calendar supports tasks
                    # For now, just use the first calendar we find
                    # In v2.0, we'll be smarter about calendar selection
                    self._calendar = cal
                    logger.info(f"Using calendar: {cal.name}")
                    break
                except Exception as e:
                    logger.debug(f"Skipping calendar: {e}")
                    continue
            
            if not self._calendar:
                raise Exception("No suitable task calendar found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            raise Exception(f"Failed to connect to Nextcloud: {e}")
    
    def _ensure_connected(self):
        """Ensure we're connected and have a calendar."""
        if not self._calendar:
            self.test_connection()
    
    def create_task(self, title: str, due: Optional[datetime] = None, 
                   description: Optional[str] = None) -> Task:
        """
        Create a new task in Nextcloud.
        
        Args:
            title: Task title/summary
            due: Due date/time (optional)
            description: Task description/notes (optional)
            
        Returns:
            Created Task object
        """
        self._ensure_connected()
        
        logger.info(f"Creating task: {title}")
        
        # Create iCalendar VTODO
        cal = Calendar()
        todo = Todo()
        
        # Required fields
        todo.add('summary', title)
        todo.add('status', 'NEEDS-ACTION')
        todo.add('uid', caldav.lib.url.make_uid())
        
        # Optional fields
        if due:
            todo.add('due', due)
        
        if description:
            todo.add('description', description)
        
        # Add to calendar
        cal.add_component(todo)
        
        # Save to Nextcloud
        ical_data = cal.to_ical()
        created_todo = self._calendar.save_todo(ical_data)
        
        logger.info(f"✅ Task created: {todo['uid']}")
        
        return Task(
            uid=str(todo['uid']),
            title=title,
            due=due,
            completed=False,
            description=description
        )
    
    def get_tasks_due_today(self) -> List[Task]:
        """
        Get all tasks due today.
        
        Returns:
            List of Task objects
        """
        self._ensure_connected()
        
        logger.info("Fetching today's tasks...")
        
        try:
            # Get today's date range
            today = date.today()
            start = datetime.combine(today, datetime.min.time())
            end = datetime.combine(today, datetime.max.time())
            
            # Search for todos due today
            # Note: caldav library's search is a bit finnicky, so we'll get all
            # todos and filter ourselves for v0.1
            todos = self._calendar.todos(include_completed=False)
            
            tasks = []
            for todo_obj in todos:
                try:
                    task = self._parse_todo(todo_obj)
                    
                    # Filter to tasks due today
                    if task.due and task.due.date() == today:
                        tasks.append(task)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse todo: {e}")
                    continue
            
            logger.info(f"Found {len(tasks)} task(s) due today")
            return sorted(tasks, key=lambda t: t.due or datetime.max)
            
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}", exc_info=True)
            raise
    
    def complete_task(self, uid: str) -> str:
        """
        Mark a task as complete.
        
        Args:
            uid: Task UID
            
        Returns:
            Task title (for confirmation message)
        """
        self._ensure_connected()
        
        logger.info(f"Completing task: {uid}")
        
        try:
            # Get all todos (includes completed for finding by UID)
            todos = self._calendar.todos(include_completed=True)
            
            # Find the specific todo
            for todo_obj in todos:
                try:
                    # Parse the ical data
                    ical = Calendar.from_ical(todo_obj.data)
                    
                    for component in ical.walk('VTODO'):
                        if str(component.get('uid')) == uid:
                            # Found it! Update status
                            component['status'] = 'COMPLETED'
                            component['completed'] = datetime.now()
                            component['percent-complete'] = 100
                            
                            # Save back to Nextcloud
                            todo_obj.data = ical.to_ical()
                            todo_obj.save()
                            
                            title = str(component.get('summary', 'Unknown task'))
                            logger.info(f"✅ Task completed: {title}")
                            return title
                            
                except Exception as e:
                    logger.debug(f"Error checking todo: {e}")
                    continue
            
            raise Exception(f"Task not found: {uid}")
            
        except Exception as e:
            logger.error(f"Failed to complete task: {e}", exc_info=True)
            raise
    
    def _parse_todo(self, todo_obj) -> Task:
        """
        Parse a CalDAV todo object into a Task.
        
        Args:
            todo_obj: CalDAV todo object
            
        Returns:
            Task object
        """
        # Parse iCalendar data
        ical = Calendar.from_ical(todo_obj.data)
        
        # Find VTODO component
        for component in ical.walk('VTODO'):
            uid = str(component.get('uid'))
            title = str(component.get('summary', 'Untitled'))
            
            # Parse due date
            due = component.get('due')
            if due:
                due = due.dt if hasattr(due, 'dt') else due
                # Convert date to datetime if needed
                if isinstance(due, date) and not isinstance(due, datetime):
                    due = datetime.combine(due, datetime.max.time())
            
            # Parse status
            status = str(component.get('status', 'NEEDS-ACTION'))
            completed = status == 'COMPLETED'
            
            # Parse completed date
            completed_date = component.get('completed')
            if completed_date:
                completed_date = completed_date.dt if hasattr(completed_date, 'dt') else completed_date
            
            # Parse description
            description = component.get('description')
            if description:
                description = str(description)
            
            # Parse priority (0 = undefined, 1 = highest, 9 = lowest)
            priority = int(component.get('priority', 0))
            
            return Task(
                uid=uid,
                title=title,
                due=due,
                completed=completed,
                completed_date=completed_date,
                description=description,
                priority=priority
            )
        
        raise ValueError("No VTODO component found in calendar data")