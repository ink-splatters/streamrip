# Album Search Sorting Implementation Specification

## Current State

**Branch:** `feat/year-sort`
**Last Commit:** `6d1913b` - Year format changed to postfix

**Current Album Display Format:**
- With year: `Album Name (2023) by Artist`
- Without year: `Album Name by Artist`

**Files Modified:**
- `streamrip/metadata/search_results.py` - AlbumSummary class
- `tests/test_search_results.py` - Tests for album display

## Scope of Work

### 1. Dynamic Sorting Feature

**Location:** `streamrip/rip/main.py` - `search_interactive()` method (line ~184)

**Requirements:**
- Implement sort mode cycling with single-key shortcut
- Three sort modes: **Default** → **Year** → **Alphabetical** → **Default**
- Rebuild menu on each sort change (Option A approach)
- Persist sort mode during session

**Sort Modes:**

1. **Default:** As returned by API (no sorting)
2. **Year:** Sort by year descending (newest first), albums without year go last (sorted alphabetically)
3. **Alphabetical:** Sort by album name A-Z

**Keyboard Shortcut:**
- Must be documented in menu title with other shortcuts
- Should not conflict with existing keys (↑/↓/j/k/SPACE/ENTER/ESC)

### 2. Display Format When Sorted by Year

**Current Format (all modes):**
```
1. Album Name (2023) by Artist
2. Another Album (2022) by Artist
3. Album Without Year by Artist
```

**Required Format in Year Sort Mode:**
```
2023 - Album Name by Artist
2022 - Another Album by Artist
Album Without Year by Artist
```

**Implementation:**
- `AlbumSummary.summarize()` must accept optional `sort_mode` parameter
- OR create separate `summarize_for_year_sort()` method
- OR `SearchResults.summaries()` modifies format based on sort mode
- Remove list numbers when in year sort (use year as visual separator)

### 3. Sort Implementation Details

**Data Flow:**
```python
# In search_interactive():
sort_mode = "default"  # Initial state

while True:
    # Sort data
    if sort_mode == "year":
        sorted_results = sort_by_year(search_results)
    elif sort_mode == "alphabetical":
        sorted_results = sort_alphabetically(search_results)
    else:
        sorted_results = search_results

    # Build menu with appropriate format
    menu_items = get_formatted_items(sorted_results, sort_mode)

    # Show menu
    menu = TerminalMenu(menu_items, ...)
    result = menu.show()

    # Check if sort key was pressed (how to detect?)
    # If yes: cycle sort_mode and continue
    # If selection made: break and proceed
```

**Challenge:** `simple-term-menu` doesn't expose key press events. Need to:
- Use `quit_keys` parameter to make sort key exit menu
- Check if menu was quit vs selection made
- If quit: cycle sort mode and rebuild
- If selection: proceed with download

### 4. Year Sorting Logic

```python
def sort_by_year(results: SearchResults) -> SearchResults:
    """
    Sort albums by year descending.
    Albums without year appear last, sorted alphabetically.
    """
    with_year = []
    without_year = []

    for album in results.results:
        if album.date_released and album.date_released != "Unknown":
            year = int(album.date_released[:4])
            with_year.append((year, album))
        else:
            without_year.append(album)

    # Sort with year by year descending
    with_year.sort(key=lambda x: x[0], reverse=True)

    # Sort without year alphabetically
    without_year.sort(key=lambda x: x.name)

    # Combine
    sorted_list = [album for _, album in with_year] + without_year

    return SearchResults(results=sorted_list)
```

### 5. Alphabetical Sorting Logic

```python
def sort_alphabetically(results: SearchResults) -> SearchResults:
    """Sort albums by name A-Z."""
    sorted_list = sorted(results.results, key=lambda x: x.name.lower())
    return SearchResults(results=sorted_list)
```

### 6. Featured Artist Handling

**Before Implementation:**
1. Check current album display from Qobuz/Deezer/Tidal
2. Search for album with featured artist (e.g., "Album by Artist feat. Guest")
3. Verify if API already includes "feat." in artist name
4. Document findings

**If NOT Already Handled:**
- Determine main artist by most common artist_id across albums in results
- Mark albums with different artist_id as collaborations
- Display format: `Album Name (2023) [feat. Guest] by Artist`

**Files to Check:**
- `streamrip/metadata/album.py` - See how `AlbumMetadata.from_*()` extracts artist
- API responses - Check raw data structure

### 7. File Template Verification

**Location:** Search for file naming patterns:
```bash
grep -r "album.*name\|{album}" streamrip/ --include="*.py"
```

**Check:**
- `streamrip/filepath_utils.py` - Path sanitization
- Config file - Default naming templates
- Ensure no template breaks with new year format

**Test:**
- Create test album with year in name
- Verify file saves correctly
- Check for path injection or special character issues

### 8. Implementation Steps

**Step 1: Add Sorting Methods**
```python
# In streamrip/metadata/search_results.py

class SearchResults:
    # ... existing code ...

    def sort_by_year(self) -> "SearchResults":
        # Implementation from section 4
        pass

    def sort_alphabetically(self) -> "SearchResults":
        # Implementation from section 5
        pass
```

**Step 2: Modify Display for Year Sort**
```python
# Option A: Add parameter to summaries()
class SearchResults:
    def summaries(self, sort_mode: str = "default") -> list[str]:
        if sort_mode == "year":
            # Format: "2023 - Album Name by Artist" (no numbers)
            return [r.summarize_year_sort() for r in self.results]
        else:
            # Format: "1. Album Name (2023) by Artist"
            return [f"{i+1}. {r.summarize()}" for i, r in enumerate(self.results)]

# In AlbumSummary class:
    def summarize_year_sort(self) -> str:
        if self.date_released and self.date_released != "Unknown":
            return f"{self.date_released[:4]} - {clean(self.name)} by {clean(self.artist)}"
        else:
            return f"{clean(self.name)} by {clean(self.artist)}"
```

**Step 3: Modify search_interactive()**
```python
# In streamrip/rip/main.py

async def search_interactive(self, source: str, media_type: str, query: str):
    client = await self.get_logged_in_client(source)

    with console.status(f"[bold]Searching {source}", spinner="dots"):
        pages = await client.search(media_type, query, limit=100)
        if len(pages) == 0:
            console.print(f"[red]No search results found for query {query}")
            return
        search_results = SearchResults.from_pages(source, media_type, pages)

    # Sorting loop (only for albums)
    if media_type == "album":
        sort_mode = "default"
        sort_key = "s"  # TBD: Choose appropriate key

        while True:
            # Apply sorting
            if sort_mode == "year":
                display_results = search_results.sort_by_year()
            elif sort_mode == "alphabetical":
                display_results = search_results.sort_alphabetically()
            else:
                display_results = search_results

            # Build menu
            shortcuts = f"↑/↓/j/k - scroll | {sort_key} - sort | SPACE - select | ENTER - download | ESC - exit"

            menu = TerminalMenu(
                display_results.summaries(sort_mode),
                preview_command=display_results.preview,
                preview_size=0.5,
                title=(
                    f"Results for {media_type} '{query}' from {source.capitalize()} [Sort: {sort_mode}]\n"
                    f"{shortcuts}"
                ),
                cycle_cursor=True,
                clear_screen=True,
                multi_select=True,
                quit_keys=(sort_key, "q"),  # Exit on sort key
            )

            chosen_ind = menu.show()

            # Check if quit (sort key pressed) or selection made
            if chosen_ind is None:
                # Check if sort key was pressed vs ESC
                # Cycle sort mode
                if sort_mode == "default":
                    sort_mode = "year"
                elif sort_mode == "year":
                    sort_mode = "alphabetical"
                else:
                    sort_mode = "default"
                continue
            else:
                # Selection made, proceed
                choices = display_results.get_choices(chosen_ind)
                await self.add_all_by_id(
                    [(source, item.media_type(), item.id) for item in choices],
                )
                break
    else:
        # Non-album media types: existing code (no sorting)
        # ... existing implementation ...
        pass
```

**Problem:** Can't distinguish between quit keys. Need alternative approach:
- Use different key that's clearly for sorting
- OR use menu's return value and check selected_index type
- OR display instructions to press 's' then show menu again

**Alternative Step 3 (Simpler):**
```python
# Show sort prompt before menu
console.print("[cyan]Press 's' to change sort order, any other key to continue")
# ... then show menu as before
# This separates sort control from selection
```

### 9. Testing Requirements

**Unit Tests:**
```python
# In tests/test_search_results.py

def test_sort_by_year():
    """Test year sorting with mixed dates."""
    albums = [
        AlbumSummary("1", "Album A", "Artist", "10", "2023-01-01"),
        AlbumSummary("2", "Album B", "Artist", "10", "2021-01-01"),
        AlbumSummary("3", "Album C", "Artist", "10", None),
        AlbumSummary("4", "Album D", "Artist", "10", "2022-01-01"),
    ]
    results = SearchResults(results=albums)
    sorted_results = results.sort_by_year()

    # Should be: 2023, 2022, 2021, then None (alphabetically)
    assert sorted_results.results[0].id == "1"  # 2023
    assert sorted_results.results[1].id == "4"  # 2022
    assert sorted_results.results[2].id == "2"  # 2021
    assert sorted_results.results[3].id == "3"  # None

def test_sort_alphabetically():
    """Test alphabetical sorting."""
    albums = [
        AlbumSummary("1", "Zebra", "Artist", "10", "2023-01-01"),
        AlbumSummary("2", "Apple", "Artist", "10", "2021-01-01"),
        AlbumSummary("3", "Middle", "Artist", "10", None),
    ]
    results = SearchResults(results=albums)
    sorted_results = results.sort_alphabetically()

    assert sorted_results.results[0].name == "Apple"
    assert sorted_results.results[1].name == "Middle"
    assert sorted_results.results[2].name == "Zebra"

def test_year_sort_display_format():
    """Test display format in year sort mode."""
    album = AlbumSummary("1", "Test", "Artist", "10", "2023-01-01")
    assert album.summarize_year_sort() == "2023 - Test by Artist"

    album_no_year = AlbumSummary("2", "Test", "Artist", "10", None)
    assert album_no_year.summarize_year_sort() == "Test by Artist"
```

**Integration Test:**
- Run actual search (requires API credentials)
- Press sort key multiple times
- Verify display changes
- Verify selection still works correctly

### 10. Code Quality Checklist

- [ ] All tests pass (`pytest tests/`)
- [ ] Ruff linting clean (`ruff check`)
- [ ] Ruff formatting applied (`ruff format`)
- [ ] No new commented-out code
- [ ] Comments are concise and necessary
- [ ] Type hints present
- [ ] Docstrings on new public methods
- [ ] Featured artist handling verified/implemented
- [ ] File template functionality verified
- [ ] Works with all providers (Qobuz, Deezer, Tidal)

### 11. Final Deliverables

**Commits (separate, logical):**
1. Add sorting methods to SearchResults class
2. Add year-sort display format to AlbumSummary
3. Implement sort cycling in search_interactive()
4. Add featured artist handling (if needed)
5. Add tests for sorting functionality
6. Update documentation/shortcuts display

**Each commit must:**
- Pass all tests
- Pass ruff checks
- Have clear commit message
- Be atomic (one feature per commit)

## Notes

- SoundCloud doesn't support album search (only track/playlist)
- Sort feature only applies to album search
- Default sort is API order (preserves relevance ranking)
- Year sort shows newest first
- Albums without year appear last in year sort
- In year sort mode, year replaces list number as visual separator
