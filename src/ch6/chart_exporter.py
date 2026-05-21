"""Multi-format Altair chart export manager.

Exports charts to PNG, SVG, and HTML formats. For PNG/SVG exports,
temporarily switches to ``vl-convert`` renderer so vegafusion-backed
charts can still produce static assets.

Provides :class:`ChartExportManager` for unified naming, batch export,
export history tracking, and status display. :func:`save_altair_chart`
is a backward-compatible convenience wrapper.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import altair as alt


class _NullContext:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ChartExportManager:
    """Manages Altair chart exports with history tracking and batch support.

    Parameters
    ----------
    output_dir:
        Default directory for exported files. Created if it doesn't exist.
    default_formats:
        Default formats to export when not specified per-chart.
    default_scale_factor:
        Default scale factor for PNG/SVG exports (multiplies base 72 PPI).

    Examples
    --------
    >>> exporter = ChartExportManager(output_dir="images/")
    >>> result = exporter.export(chart, "my_chart", display=True)
    >>> batch_results = exporter.export_batch({
    ...     "chart1": chart1,
    ...     "chart2": chart2,
    ... })
    >>> exporter.display_status()
    >>> for path in exporter.list_exports():
    ...     print(path.name)
    """

    def __init__(
        self,
        output_dir: Union[str, Path],
        *,
        default_formats: Tuple[str, ...] = ("png", "svg", "html"),
        default_scale_factor: float = 2.0,
    ) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._default_formats = default_formats
        self._default_scale_factor = default_scale_factor
        self._history: List[Dict[str, Any]] = []

    @property
    def output_dir(self) -> Path:
        """The default output directory."""
        return self._output_dir

    @property
    def history(self) -> List[Dict[str, Any]]:
        """List of export history entries."""
        return list(self._history)

    @property
    def export_count(self) -> int:
        """Total number of charts exported."""
        return len(self._history)

    def export(
        self,
        chart,
        stem: str,
        *,
        formats: Optional[Tuple[str, ...]] = None,
        scale_factor: Optional[float] = None,
        output_dir: Optional[Union[str, Path]] = None,
        display: bool = False,
    ) -> Dict[str, Any]:
        """Export a single chart to specified formats.

        Parameters
        ----------
        chart:
            Altair chart object to export.
        stem:
            Filename stem (without extension).
        formats:
            Formats to export. Defaults to ``default_formats``.
        scale_factor:
            Scale factor for PNG/SVG. Defaults to ``default_scale_factor``.
        output_dir:
            Override output directory for this export.
        display:
            If True, display the saved paths after export.

        Returns
        -------
        dict
            Result dict with keys:
            - ``success`` (bool): True if all formats exported successfully
            - ``errors`` (list): List of (format, error_message) tuples for failed exports
            - ``paths`` (dict): Mapping of format -> saved file path
            - ``chart_id`` (str): The stem name
        """
        target_dir = Path(output_dir) if output_dir else self._output_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        active_formats = formats or self._default_formats
        active_scale = scale_factor or self._default_scale_factor

        saved: Dict[str, str] = {}
        errors: List[Tuple[str, str]] = []

        for fmt in active_formats:
            target = target_dir / f"{stem}.{fmt}"
            try:
                if fmt == "html":
                    chart.save(str(target))
                else:
                    try:
                        if "vl-convert" in alt.renderers.names():
                            ctx = alt.renderers.enable(
                                "vl-convert", ppi=72 * active_scale
                            )
                        else:
                            ctx = _NullContext()
                        with ctx:
                            chart.save(str(target))
                    except Exception:
                        chart.save(str(target))
                saved[fmt] = str(target)
            except Exception as e:
                errors.append((fmt, str(e)))

        entry = {
            "stem": stem,
            "chart_id": stem,
            "formats": active_formats,
            "paths": saved,
            "scale_factor": active_scale,
            "output_dir": str(target_dir),
            "success": len(errors) == 0,
            "errors": errors,
        }
        self._history.append(entry)

        result = {
            "success": len(errors) == 0,
            "errors": errors,
            "paths": saved,
            "chart_id": stem,
        }

        if display:
            if result["success"]:
                print(f"Exported '{stem}':")
                for fmt, path in saved.items():
                    print(f"  {fmt}: {path}")
            else:
                print(f"Export '{stem}' had errors:")
                for fmt, err in errors:
                    print(f"  {fmt}: {err}")

        return result

    def export_batch(
        self,
        items: Union[Dict[str, Any], List[Tuple]],
        *,
        formats: Optional[Tuple[str, ...]] = None,
        scale_factor: Optional[float] = None,
        output_dir: Optional[Union[str, Path]] = None,
        display: bool = False,
    ) -> List[Dict[str, Any]]:
        """Export multiple charts in batch.

        Parameters
        ----------
        items:
            Either a dict mapping ``chart_id -> chart``, or a list of
            ``(chart, stem)`` tuples.
        formats:
            Default formats for all items.
        scale_factor:
            Default scale factor for all items.
        output_dir:
            Default output directory for all items.
        display:
            If True, print summary after batch export.

        Returns
        -------
        list[dict]
            List of result dicts, one per item. Each dict has keys:
            - ``success`` (bool)
            - ``errors`` (list)
            - ``paths`` (dict)
            - ``chart_id`` (str)
        """
        if isinstance(items, dict):
            item_list = [(chart, stem) for stem, chart in items.items()]
        else:
            item_list = items

        results = []
        for chart, stem in item_list:
            result = self.export(
                chart,
                stem,
                formats=formats,
                scale_factor=scale_factor,
                output_dir=output_dir,
                display=False,
            )
            results.append(result)

        if display:
            success_count = sum(1 for r in results if r["success"])
            print(f"Batch export: {success_count}/{len(results)} succeeded")
            for r in results:
                status = "OK" if r["success"] else "FAILED"
                print(f"  {r['chart_id']}: {status}")
                if not r["success"]:
                    for fmt, err in r["errors"]:
                        print(f"    {fmt}: {err}")

        return results

    def get_status(self) -> Dict[str, Any]:
        """Return a status summary dict.

        Returns
        -------
        dict
            Keys: ``export_count``, ``output_dir``, ``recent_exports``.
        """
        return {
            "export_count": self.export_count,
            "output_dir": str(self._output_dir),
            "recent_exports": [
                {"stem": e["stem"], "formats": e["formats"]}
                for e in self._history[-5:]
            ],
        }

    def display_status(self) -> None:
        """Display export status in a notebook-friendly format.

        Shows total exports, output directory, and recent exports.
        """
        try:
            from IPython.display import HTML, display

            status = self.get_status()
            html = [
                f"<strong>Export Status</strong>",
                f"<ul>",
                f"  <li><strong>Total exports:</strong> {status['export_count']}</li>",
                f"  <li><strong>Output directory:</strong> {status['output_dir']}</li>",
                f"</ul>",
            ]
            if status["recent_exports"]:
                html.append("<strong>Recent exports:</strong>")
                html.append("<ul>")
                for e in status["recent_exports"]:
                    formats_str = ", ".join(e["formats"])
                    html.append(f"  <li>{e['stem']} ({formats_str})</li>")
                html.append("</ul>")
            display(HTML("\n".join(html)))
        except Exception:
            status = self.get_status()
            print(f"Export Status:")
            print(f"  Total exports: {status['export_count']}")
            print(f"  Output directory: {status['output_dir']}")
            if status["recent_exports"]:
                print(f"  Recent exports:")
                for e in status["recent_exports"]:
                    formats_str = ", ".join(e["formats"])
                    print(f"    - {e['stem']} ({formats_str})")

    def list_exports(self) -> List[Path]:
        """List all exported files in the output directory.

        Returns
        -------
        list[Path]
            List of Path objects for all exported files.
        """
        files = []
        for entry in self._history:
            for fmt, path_str in entry["paths"].items():
                files.append(Path(path_str))
        return files

    def print_history(self) -> None:
        """Print export history to stdout in a readable table format."""
        if not self._history:
            print("No exports recorded.")
            return

        print(f"Export History ({self.export_count} total):")
        print("-" * 60)
        for i, entry in enumerate(self._history, 1):
            formats_str = ", ".join(entry["formats"])
            print(f"  {i:>3}. {entry['stem']}")
            print(f"       formats: {formats_str}")
            print(f"       dir:     {entry['output_dir']}")
            for fmt, path in entry["paths"].items():
                print(f"       {fmt}: {path}")
        print("-" * 60)


def save_altair_chart(
    chart,
    output_dir: Union[str, Path],
    stem: str,
    *,
    formats: Tuple[str, ...] = ("png", "svg", "html"),
    scale_factor: float = 2.0,
) -> Dict[str, str]:
    """Save an Altair chart to PNG / SVG / HTML — backward-compatible wrapper.

    This is a thin wrapper around :class:`ChartExportManager.export` for
    code that prefers a simple function call. For batch exports, history
    tracking, and status display, use :class:`ChartExportManager` directly.

    Parameters
    ----------
    chart:
        Altair chart object to export.
    output_dir:
        Directory to save exported files. Created if it doesn't exist.
    stem:
        Filename stem (without extension) for the exported files.
    formats:
        Tuple of formats to export. Default: ``("png", "svg", "html")``.
    scale_factor:
        Scale factor for PNG/SVG exports (multiplies base 72 PPI).

    Returns
    -------
    dict
        Mapping of format -> saved file path.

    See Also
    --------
    ChartExportManager: Full-featured export manager with history and batch.
    """
    manager = ChartExportManager(
        output_dir=output_dir,
        default_formats=formats,
        default_scale_factor=scale_factor,
    )
    result = manager.export(chart, stem)
    return result["paths"]
