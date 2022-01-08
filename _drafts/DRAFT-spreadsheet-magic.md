---
layout: post
title: "Spreadsheet magic"
image_link_base: /assets/img/drafts/
---
I once stumbled upon a quote "if people knew how to use grep, awk, 
sed, and xargs, half of the applications would never need to be created." I think roughly the same can be said about
spreadsheets - knowing how to use just a few features and functions allows handling quite complex use cases within
just a few hours. In this post, I'll cover a few of those most-useful-but-a-bit-complex spreadsheet's functions and 
features and show how they combine to build a "habit tracker" spreadsheet.

# What we are building

First, let's cover the use cases for the habit tracker. Long story short, a habit tracker is an app (or tool) that helps
develop (or quit) a habit: "read at least 30 min a day," or "quit smoking." Habit trackers support inner 
motivation to do so with "external" reinforcement:

* rewarding good behaviors via "green tick "effect" - ticking a checkbox or crossing an item grants some sense 
  of accomplishment 
* reducing perceived "toughness" of the task - "I will do this **for two months**" is a lot harder than
  "I will do this **today**" for the same two months. 

Here are the use cases our habit tracker sheet would need to fulfill:

* Support habits that need to happen every day, or only on some days of week/month.
* Support qualitative and quantitative habits.
* Allow setting goals for habits - for example, "run 20 km a month" or "read for 30 min every day".
* Clearly show current progress towards the goal and remaining "distance."
* Enable "green tick" and "do today" effects.

# Spreadsheet

Here's the result - [Habit Tracker spreadsheet][spreadsheet]. I dare to assume using it is quite
self-explanatory - add/remove the goals by inserting/removing columns on the `Template` sheet, putting the weekly 
schedule onto the `Technical` sheet, adjust conditional formatting if something becomes off[^1], copy the 
`Template` sheet, set the day you want to start, and off you go.

[
    ![
    Screenshot showing a partially filled habit tracker spreadsheet for January 2022.
    The date on the screenshot is January 8th, 2022.
    The first row contains headers: Date, DOW, Day of Week, and finally Habit 1 to Habit 7.
    Date column contains dates starting with January 1st, 2022. About 20 dates are visible.
    The following two columns contain days of week numbers (DOW column) and names (Day Of Week column)
    Habits 1, 2, and 3 have a weekly schedule. 1st and 3rd habit have "days off" on weekends - 
    the corresponding cells have blue fill and letter N. Habit 2 also has Tuesday and Thursday off,
    with similar cell contents and formatting. Cells with any value except N
    have a green color fill. Empty cells in rows 2022-01-07 and earlier have a red color fill; 
    empty cells in rows starting with 2022-01-08 have no color fill.
    Habits 4 to 7 are "everyday" habits and have checkboxes in the cells associated with them. If the
    checkbox is marked, the cell has a green fill. Otherwise, cells that are "in the past" have red fill. 
    ]({{ page.image_link_base }}/habit_tracker.png)
]({{ page.image_link_base }}/habit_tracker.png)

Now that we have a result in view, let's finally talk about technical stuff - features and formulas used to 
build it. I'll omit the very basics (like cross-tab references, references with fixed row/column, well-known
functions, etc.) and focus on the most powerful and complex to use. All cell references are on the 
`Template` tab, unless the sheet is explicitly specified.

[spreadsheet]: https://bit.ly/3F6EwJr

[^1]: Common source of issues is moving the content - spreadsheets are not always intelligent enough to adjust formulas
    and conditional formatting when source data moves. However, adding/removing columns is more robust, so try to 
    use it as much as possible.

## Formulas

### Sequence

[`SEQUENCE`][sequence] function - fills the specified number of rows and columns with sequential values with a 
specified step.

**Example:** `SEQUENCE(1, 5, 0, 2)` - creates a (1-column x 5-row) block with [0, 2, 4, 6, 8] values 

**Used at**  cell `A7` to automatically create a column of dates in the selected month.

[sequence]: https://support.google.com/docs/answer/9368244

### HLOOKUP & VLOOKUP

[`VLOOKUP(search_key, range, index, is_sorted)`][vlookup] is a powerhouse behind many tricks that look  
magical. The simplest way to explain it is to imagine that the `range` becomes an isolated sheet. First, the `index` 
argument selects a column from that "virtual sheet." Then, `search_query` is looked up in the first column of the 
"virtual sheet." If VLOOKUP finds the match, it returns the value of a cell that resides at an intersection of this 
row and the selected column. `is_sorted` makes this lookup "inexact" and select the row with the nearest match - 
the largest value that is less or equal to the search key.

[`HLOOKUP`][hlookup] does the same, except it fixes the row and searches in the first row to select a column. 

**Example:** 
* `VLOOKUP(A10, Technical!B7:D25, 3, FALSE)` - looks up exact value of `A10` in `Technical!B7:B25` and 
if found returns the value of a cell in a `D` column  

**Used at:**
* Cells `C7:C37` looks up weekday name by weekday number[^2].
* Cells `D7:F37` use VLOOKUP in conjunction with `IF` to apply the weekly schedule to the goals.

[^2]: This could be achieved without VLOOKUP by text formatting `TEXT(value, "dddd")`... Unless you need names from a
    different locale/language

[vlookup]: https://support.google.com/docs/answer/3093318
[hlookup]: https://support.google.com/docs/answer/3093375

### INDIRECT, ADDRESS, ROW & COLUMN

[`INDIRECT`][indirect] returns the cell's value by the address. Simple put `INDIRECT("B2")` becomes the 
value of `B2`. It might look redundant at a glance (`=B2` does the same, and is much simpler), but `INDIRECT` starts 
to shine when used with an alternative reference mode `INDIRECT("R1C1"; FALSE)` or in conjunction with `ADDRESS`.

[`ADDRESS`][address] takes row and column umber numbers and returns the cell address. 

[`ROW`][row] and [`COLUMN`][column] simply returns the row and column of a cell, both 1-based[^3]. Calling them 
without arguments return the values of a current cell.

**Examples:** 
* `INDIRECT("RC[-1]"; FALSE)` - returns the value of a cell to the left.
* `INDIRECT(ADDRESS(ROW()+2; COLUMN();;;"Technical"))` - fetch value from a `Technical` tab and 2 rows below. 
  E.g. `C2` becomes `Technical!C4`[^4].  
* `INDIRECT(ADDRESS(COLUMN(); ROW();;;"Technical"))` - fetch value from a `Technical` tab and "transpose" the address  
  E.g. `C2` => `Technical!B3`, `D7` => `Technical!G4`. Quite handy if "values" on one tab needs to become column headers
  on the other (yes, similar to pivot table).

**Used at:**
* Limited use of `COLUMN` in cells `D7:F37` - practically could've done without it.
* **A lot** of uses for conditional formatting, which we'll cover in the corresponding section.

[indirect]: https://support.google.com/docs/answer/3093377
[address]: https://support.google.com/docs/answer/3093308
[row]: https://support.google.com/docs/answer/3093316
[column]: https://support.google.com/docs/answer/3093373

[^3]: i.e. for cell `A1` both `ROW` and `COLUMN` return 1, not 0.
[^4]: This can be easier achieved by using a reference + "pulling" the cells

### "Open" range references

Range references are widely known and don't need explanation. However, there are less-known reference styles that can 
come in quite handy.

**Examples:**
* `A7:A` - `A7` and rest of the `A` column. Similarly, `C7:7` - entire 7th row, starting with column `C` 
* `B12:G` - columns from `b` to `G`, starting with 12th row.

**Used at:**
* Cells `D3:D7` use `D7:D` to sum all the records in the column.

## Conditional formatting

Conditional formatting makes the dry and terse spreadsheet(s) speak to the emotional structures in the brain. 
With conditional formatting (and a little we can finally make the "green tick" effect work. Two sets of conditional 
formatting rules exist in the tracker sheet: one for "habits with a weekly schedule" and the other for "everyday" habits. 

**Note:** conditional formatting rules are evaluated sequentially and terminate after the 
first matching condition.

**Weekly schedule ruleset:**
* If cell value equals `N` - blue fill
* If the cell contains data - green field
* Custom formula "if a date is in the past" - red fill.

**Every day ruleset:**
* If equal to `True` - green fill
* Custom formula "if a date is in the past" - red fill.

The "if a date is in the past" formula is probably the most complex thing in this entire sheet. Here goes:

```
=AND(
  NOT(ISBLANK(
    INDIRECT(ADDRESS(ROW(); 1))
  ));
  TODAY()>INDIRECT(ADDRESS(ROW(); 1))
)
```

In plain English: "if the first cell in the row is not empty and its value is smaller than today's date."

# Recap

Here's how the various features listed above contribute to achieving the use cases we listed.

| Use case                         | Featute                                                 |
|----------------------------------|---------------------------------------------------------|
| Weekly and every day habits      | `VLOOKUP` + `WEEKDAY`                                   |
| Qualitative habits               | Checkboxes                                              |
| Quantitative habits              | Don't need special support                              |
| Setting goals, tracking progress | Row with goals + `SUM` with "open" range                |
| "Green tick" effect              | Conditional formatting + `INDIRECT` + `ROW`             |
| "Do today" effect                | `SEQUENCE` + Conditional formatting + `INDIRECT` + `ROW` |

# Extras

Other spreadsheet features you might want to have in your toolbelt:

**Pivot table** - a very flexible and powerful instrument to aggregate data, and even more so if used in conjunction 
with VLOOKUP. Record what you eat and how much, VLOOKUP nutrition data, aggregate per day with pivot table, pull onto a
separate tab, add target values via VLOOKUP again, compare actual with targets - here's your diet monitor[^5].

**Relative references** - also know as RC-format. Only work with `INDIRECT`, but can be extremely handy for 
sophisticated conditional formatting scenarios. For example:
* fill red if cell to the right is larger than `B2` - `=INDIRECT("RC1"; False) < B2`
* fill green if current cell is larger than 0,5 * `B2` - `=INDIRECT("RC"; False) > 0,5 * B2`

[^5]: the challenge here is to obtain nutrition information and carefully record what you eat. 
    The rest is pretty mechanical. 

# Conclusion

This spreadsheet has almost complete feature parity with one of the paid habit tracker apps - and only
took 2.5-3 hours to create. Mastering just a few spreadsheet features (and googling the others) allows supporting
many use cases that otherwise require a dedicated app. Moreover, you get to customize your solution as you
please, export in virtually any format you like, share, comment, collaborate, etc., etc., etc., out of the box.

Practically, even moderately complex spreadsheets can cover more complex scenarios from a variety of areas -
financial modeling, project prioritization, evaluating job offers, stock picking, and many more.
