"""
ui/floating/dock_manager.py – Clean docking manager with stable snapping.
"""

import math
import time
from typing import List, Optional, Tuple, Any

from core.logger import activity_log


class DockGroup:
    """A group of docked windows with stored offsets."""
    
    def __init__(self, leader):
        self.leader = leader
        self.members: List[Any] = [leader]
        self.offsets: dict = {}  # window -> (dx, dy) from leader
        self._update_offsets()
    
    def _update_offsets(self):
        lx, ly = self.leader.top.winfo_x(), self.leader.top.winfo_y()
        for member in self.members:
            x, y = member.top.winfo_x(), member.top.winfo_y()
            self.offsets[member] = (x - lx, y - ly)
    
    def add_member(self, window):
        if window not in self.members:
            self.members.append(window)
            window.group = self
            window.group_leader = self.leader
            self._update_offsets()
    
    def remove_member(self, window):
        if window in self.members:
            self.members.remove(window)
            window.group = None
            window.group_leader = None
            if len(self.members) <= 1:
                # Dissolve group
                if self.leader:
                    self.leader.group = None
                    self.leader.group_leader = None
                return None
            self._update_offsets()
        return self
    
    def move_by(self, dx: int, dy: int):
        """Move the entire group by (dx, dy) from current positions."""
        lx, ly = self.leader.top.winfo_x(), self.leader.top.winfo_y()
        self.leader.top.geometry(f"+{lx + dx}+{ly + dy}")
        # Force update so we read fresh coordinates
        self.leader.top.update_idletasks()
        new_lx, new_ly = self.leader.top.winfo_x(), self.leader.top.winfo_y()
        for member in self.members:
            if member is self.leader:
                continue
            ox, oy = self.offsets.get(member, (0, 0))
            member.top.geometry(f"+{new_lx + ox}+{new_ly + oy}")
    
    def contains(self, window) -> bool:
        return window in self.members
    
    def __len__(self):
        return len(self.members)


class DockManager:
    """Singleton manager for docking operations."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.groups: List[DockGroup] = []
        self._last_snap_time = 0
        self.DOCK_THRESHOLD = 30
        self.UNDOCK_THRESHOLD = 80
    
    def register(self, window):
        if hasattr(window, 'group') and window.group:
            if window.group not in self.groups:
                self.groups.append(window.group)
    
    def unregister(self, window):
        if hasattr(window, 'group') and window.group:
            group = window.group
            group.remove_member(window)
            if len(group) <= 1:
                if group in self.groups:
                    self.groups.remove(group)
                if group.leader and hasattr(group.leader, 'group'):
                    group.leader.group = None
                    group.leader.group_leader = None
    
    def get_or_create_group(self, window) -> DockGroup:
        if hasattr(window, 'group') and window.group:
            return window.group
        group = DockGroup(window)
        window.group = group
        window.group_leader = window
        self.groups.append(group)
        return group
    
    def merge_groups(self, group1: DockGroup, group2: DockGroup):
        if group1 is group2:
            return
        for member in group2.members:
            if member not in group1.members:
                group1.members.append(member)
                member.group = group1
                member.group_leader = group1.leader
        group1._update_offsets()
        if group2 in self.groups:
            self.groups.remove(group2)
        group2.leader = None
        group2.members = []
        group2.offsets = {}
    
    def undock(self, window):
        if hasattr(window, 'group') and window.group:
            group = window.group
            group.remove_member(window)
            if len(group) <= 1:
                if group in self.groups:
                    self.groups.remove(group)
                if group.leader and hasattr(group.leader, 'group'):
                    group.leader.group = None
                    group.leader.group_leader = None
            window.group = None
            window.group_leader = None
            activity_log.log("undock", window.title_text, "")
    
    def find_best_snap(self, window, others: List[Any]) -> Tuple[Optional[Any], Optional[Tuple[int, int]]]:
        """
        Find the best window to snap to.
        Returns (target_window, (new_x, new_y)).
        """
        # Debounce to avoid rapid re-snapping
        now = time.time()
        if now - self._last_snap_time < 0.3:
            return None, None
        
        x1, y1 = window.top.winfo_x(), window.top.winfo_y()
        w1, h1 = window.top.winfo_width(), window.top.winfo_height()
        
        best_target = None
        best_new_pos = None
        best_dist = float('inf')
        best_edge = None  # 'left','right','top','bottom' for debug
        
        for other in others:
            if other is window:
                continue
            # Skip if already in same group
            if hasattr(window, 'group') and window.group:
                if hasattr(other, 'group') and other.group and window.group is other.group:
                    continue
            
            x2, y2 = other.top.winfo_x(), other.top.winfo_y()
            w2, h2 = other.top.winfo_width(), other.top.winfo_height()
            
            # Skip overlapping windows
            overlap_x = min(x1 + w1, x2 + w2) - max(x1, x2)
            overlap_y = min(y1 + h1, y2 + h2) - max(y1, y2)
            if overlap_x > 0 and overlap_y > 0:
                continue
            
            # Compute gaps for all four edges
            left_gap = x1 - (x2 + w2) if x1 > x2 + w2 else float('inf')
            right_gap = x2 - (x1 + w1) if x2 > x1 + w1 else float('inf')
            top_gap = y1 - (y2 + h2) if y1 > y2 + h2 else float('inf')
            bottom_gap = y2 - (y1 + h1) if y2 > y1 + h1 else float('inf')
            
            candidates = []
            if left_gap <= self.DOCK_THRESHOLD:
                candidates.append((left_gap, 'left', x2 + w2, y1))  # snap right of other
            if right_gap <= self.DOCK_THRESHOLD:
                candidates.append((right_gap, 'right', x2 - w1, y1))  # snap left of other
            if top_gap <= self.DOCK_THRESHOLD:
                candidates.append((top_gap, 'top', x1, y2 + h2))  # snap below other
            if bottom_gap <= self.DOCK_THRESHOLD:
                candidates.append((bottom_gap, 'bottom', x1, y2 - h1))  # snap above other
            
            if not candidates:
                continue
            
            # Choose the candidate with the smallest gap
            gap, edge, nx, ny = min(candidates, key=lambda c: c[0])
            if gap < best_dist:
                best_dist = gap
                best_target = other
                best_new_pos = (nx, ny)
                best_edge = edge
        
        if best_target is not None:
            self._last_snap_time = time.time()
        return best_target, best_new_pos

    def try_dock(self, window) -> bool:
        """Attempt to dock the window. Returns True if docked."""
        # If window is already in a group with more than one member, it's already docked
        if hasattr(window, 'group') and window.group and len(window.group) > 1:
            # Already docked – no need to try again
            return False
        
        others = [w for w in window._all_windows if w is not window]
        target, new_pos = self.find_best_snap(window, others)
        if target is None or new_pos is None:
            return False
        
        nx, ny = new_pos
        
        # Move the window (or its group) to the snapped position
        dx = nx - window.top.winfo_x()
        dy = ny - window.top.winfo_y()
        
        if window.group:
            window.group.move_by(dx, dy)
        else:
            window.top.geometry(f"+{nx}+{ny}")
            window.top.update_idletasks()  # ensure geometry is applied
        
        # Merge groups
        if window.group is None:
            group = self.get_or_create_group(window)
            if target.group is None:
                group.add_member(target)
            else:
                self.merge_groups(group, target.group)
        else:
            if target.group is None:
                window.group.add_member(target)
            else:
                self.merge_groups(window.group, target.group)
        
        return True


# Singleton instance
dock_manager = DockManager()
