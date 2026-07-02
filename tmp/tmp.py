    def _handle_completion(self, completed_at: float | None = None) -> None:
        if self._completion_handled:
            # Already handled, but we still want to show the overdue popup if not present
            self._show_overdue_popup()
            return
        self._completion_handled = True
        # ... rest unchanged