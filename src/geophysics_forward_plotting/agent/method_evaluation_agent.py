"""MethodEvaluationAgent：自动评估一个新方法相对其他方法的优势与缺点。

给定
----
- 新方法的结果数组（可选运行时间）
- 若干基线方法的结果数组（可选运行时间）
- 可选的参考解（ground truth / 解析解）

自动产出
--------
1. 多方法并排对比图（统一色标，一目了然谁更接近参考）
2. 新方法 vs 参考解的误差图（若提供参考）
3. 新方法 vs 每个基线的残差图（差异在物理空间的分布）
4. 性能柱状图（若每个方法都提供了 runtime）
5. 定量指标：RMSE、最大绝对误差、相关系数、运行时间
6. 自动生成的"优势 / 缺点"结论（基于上述指标排名）

设计原则
--------
- 不重新实现绘图：所有图件都通过 PlottingAgent 复用已有 Skill，
  因此自动继承几何约定与 FigureReviewSkill 规范检查。
- 纯编排层：唯一新增的是指标计算与结论生成。

用法示例
--------
>>> from geophysics_forward_plotting.agent import MethodEvaluationAgent, MethodResult
>>> agent = MethodEvaluationAgent()
>>> report = agent.evaluate(
...     new_method=MethodResult("New FWI", new_arr, runtime=12.3),
...     baselines=[MethodResult("RTM", rtm_arr, runtime=8.1)],
...     reference=true_arr,
...     figure_kind="shot_record",
...     dx=0.01, dt=0.001,
... )
>>> print(report.summary)
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from geophysics_forward_plotting.agent.plotting_agent import PlottingAgent
from geophysics_forward_plotting.core.exceptions import DataValidationError
from geophysics_forward_plotting.core.models import DataContext, FigureResult, FigureTask

NumericArray = NDArray[np.floating[Any] | np.integer[Any]]

# figure_kind -> (默认 x 轴标签, 默认 y 轴标签)
_KIND_LABELS: dict[str, tuple[str, str]] = {
    "shot_record": ("Distance (km)", "Time (s)"),
    "wavefield_snapshot": ("Distance (km)", "Depth (km)"),
    "velocity_model": ("Distance (km)", "Depth (km)"),
}


@dataclass(slots=True)
class MethodResult:
    """单个方法的结果及可选元数据。"""

    name: str
    data: NumericArray
    runtime: float | None = None  # 运行时间（秒），用于性能对比图


@dataclass(slots=True)
class MethodMetrics:
    """单个方法相对参考解的定量指标。"""

    rmse: float | None = None  # 均方根误差（需要参考解）
    max_abs_error: float | None = None  # 最大绝对误差
    correlation: float | None = None  # 与参考解的相关系数
    runtime: float | None = None  # 运行时间（秒）

    def as_dict(self) -> dict[str, float | None]:
        return {
            "rmse": self.rmse,
            "max_abs_error": self.max_abs_error,
            "correlation": self.correlation,
            "runtime": self.runtime,
        }


@dataclass(slots=True)
class EvaluationReport:
    """方法评估的完整结果。"""

    saved_paths: list[Path] = field(default_factory=list)
    metrics: dict[str, MethodMetrics] = field(default_factory=dict)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    review_messages: list[str] = field(default_factory=list)
    summary: str = ""

    def render_text(self) -> str:
        """生成可直接打印的评估报告文本。"""
        lines = [self.summary, ""]
        lines.append("Metrics")
        lines.append("-" * 60)
        header = f"  {'Method':<18}{'RMSE':>12}{'MaxErr':>12}{'Corr':>8}{'Time(s)':>10}"
        lines.append(header)
        for name, m in self.metrics.items():
            rmse = "n/a" if m.rmse is None else f"{m.rmse:.4g}"
            mae = "n/a" if m.max_abs_error is None else f"{m.max_abs_error:.4g}"
            corr = "n/a" if m.correlation is None else f"{m.correlation:.4f}"
            rt = "n/a" if m.runtime is None else f"{m.runtime:.3f}"
            lines.append(f"  {name:<18}{rmse:>12}{mae:>12}{corr:>8}{rt:>10}")
        lines.append("")
        lines.append("Strengths")
        lines.append("-" * 60)
        lines.extend(f"  [+] {s}" for s in self.strengths) or lines.append("  (none)")
        lines.append("")
        lines.append("Weaknesses")
        lines.append("-" * 60)
        lines.extend(f"  [-] {w}" for w in self.weaknesses) or lines.append("  (none)")
        lines.append("")
        lines.append(f"Figures saved: {len(self.saved_paths)}")
        for p in self.saved_paths:
            lines.append(f"  {p}")
        return "\n".join(lines)


@dataclass(slots=True)
class MethodEvaluationAgent:
    """评估新方法相对基线方法的优势与缺点，自动出图 + 出指标 + 出结论。"""

    plotting_agent: PlottingAgent = field(default_factory=PlottingAgent)

    def evaluate(
        self,
        new_method: MethodResult,
        baselines: Sequence[MethodResult],
        *,
        reference: NumericArray | None = None,
        figure_kind: str = "shot_record",
        output_dir: Path | str = "outputs/evaluation",
        colorbar_label: str = "Amplitude",
        x_label: str | None = None,
        y_label: str | None = None,
        dx: float | None = None,
        dz: float | None = None,
        dt: float | None = None,
        dpi: int = 300,
        export_formats: tuple[str, ...] = ("png",),
    ) -> EvaluationReport:
        """执行完整评估流程并返回报告。"""
        if not baselines:
            raise DataValidationError("至少需要一个基线方法用于对比")

        methods = [new_method, *baselines]
        self._validate_shapes(methods, reference)

        xl, yl = _KIND_LABELS.get(figure_kind, ("Distance (km)", "Depth (km)"))
        x_label = x_label or xl
        y_label = y_label or yl
        out = Path(output_dir)
        # 误差图纵轴：炮记录用时间步长，空间场用深度步长
        vertical = dt if figure_kind == "shot_record" else dz

        report = EvaluationReport()

        # 1) 定量指标
        report.metrics = self._compute_metrics(methods, reference)

        # 2) 多方法并排对比图（最多 4 个面板）
        report.saved_paths += self._comparison_figure(
            methods, out, figure_kind, colorbar_label, x_label, y_label,
            dx, vertical, dpi, export_formats, report,
        )

        # 3) 新方法 vs 参考解的误差图
        if reference is not None:
            report.saved_paths += self._error_figure(
                pred=new_method.data, ref=reference,
                stem_dir=out / "error_vs_reference",
                title=f"{new_method.name} - Reference",
                colorbar_label="Signed Error",
                x_label=x_label, y_label=y_label,
                dx=dx, vertical=vertical, dpi=dpi,
                export_formats=export_formats, report=report,
            )

        # 4) 新方法 vs 每个基线的残差图
        for base in baselines:
            report.saved_paths += self._error_figure(
                pred=new_method.data, ref=base.data,
                stem_dir=out / f"residual_vs_{_slug(base.name)}",
                title=f"{new_method.name} - {base.name}",
                colorbar_label="Residual",
                x_label=x_label, y_label=y_label,
                dx=dx, vertical=vertical, dpi=dpi,
                export_formats=export_formats, report=report,
            )

        # 5) 性能柱状图（需所有方法都有 runtime）
        if all(m.runtime is not None for m in methods):
            report.saved_paths += self._performance_figure(
                methods, out, dpi, export_formats, report,
            )

        # 6) 结论：优势 / 缺点
        self._derive_verdict(new_method, baselines, report, has_reference=reference is not None)

        report.summary = self._summary_line(new_method, baselines, report)
        return report

    # ── 内部步骤 ────────────────────────────────────────────────

    @staticmethod
    def _validate_shapes(methods: list[MethodResult], reference: NumericArray | None) -> None:
        ref_shape = methods[0].data.shape
        for m in methods:
            if m.data.shape != ref_shape:
                raise DataValidationError(
                    f"方法 '{m.name}' 的形状 {m.data.shape} 与 '{methods[0].name}' "
                    f"的形状 {ref_shape} 不一致"
                )
        if reference is not None and reference.shape != ref_shape:
            raise DataValidationError(
                f"参考解形状 {reference.shape} 与方法结果形状 {ref_shape} 不一致"
            )

    @staticmethod
    def _compute_metrics(
        methods: list[MethodResult], reference: NumericArray | None
    ) -> dict[str, MethodMetrics]:
        metrics: dict[str, MethodMetrics] = {}
        ref = None if reference is None else reference.astype(float)
        for m in methods:
            mm = MethodMetrics(runtime=m.runtime)
            if ref is not None:
                diff = m.data.astype(float) - ref
                mm.rmse = float(np.sqrt(np.mean(diff**2)))
                mm.max_abs_error = float(np.max(np.abs(diff)))
                a = m.data.astype(float).ravel()
                b = ref.ravel()
                if a.std() > 0 and b.std() > 0:
                    mm.correlation = float(np.corrcoef(a, b)[0, 1])
            metrics[m.name] = mm
        return metrics

    def _comparison_figure(
        self, methods, out, figure_kind, colorbar_label, x_label, y_label,
        dx, vertical, dpi, export_formats, report,
    ) -> list[Path]:
        panel = methods[:4]
        if len(methods) > 4:
            report.review_messages.append(
                f"[INFO] 对比图最多 4 个面板，已显示前 4 个方法（共 {len(methods)} 个）"
            )
        task = FigureTask(
            task_type="multi_method_comparison",
            title="Method Comparison",
            output_dir=out,
            x_label=x_label,
            y_label=y_label,
            colorbar_label=colorbar_label,
            method_names=tuple(m.name for m in panel),
            symmetric_clim=True,
            dx=dx, dz=vertical, dpi=dpi,
            export_formats=export_formats,
        )
        ctx = DataContext(raw_data=tuple(m.data for m in panel))
        return self._run(task, ctx, report)

    def _error_figure(
        self, *, pred, ref, stem_dir, title, colorbar_label,
        x_label, y_label, dx, vertical, dpi, export_formats, report,
    ) -> list[Path]:
        task = FigureTask(
            task_type="error_map",
            title=title,
            output_dir=stem_dir,
            x_label=x_label,
            y_label=y_label,
            colorbar_label=colorbar_label,
            dx=dx, dz=vertical, dpi=dpi,
            export_formats=export_formats,
            parameters={"error_mode": "signed"},
        )
        ctx = DataContext(raw_data=(pred, ref))
        return self._run(task, ctx, report)

    def _performance_figure(self, methods, out, dpi, export_formats, report) -> list[Path]:
        task = FigureTask(
            task_type="performance",
            title="Runtime Comparison",
            output_dir=out,
            method_names=tuple(m.name for m in methods),
            dpi=dpi,
            export_formats=export_formats,
            parameters={
                "values": [float(m.runtime) for m in methods],
                "metric_label": "Runtime (s)",
            },
        )
        return self._run(task, DataContext(), report)

    def _run(self, task: FigureTask, ctx: DataContext, report: EvaluationReport) -> list[Path]:
        result: FigureResult = self.plotting_agent.run(task, ctx)
        report.review_messages.extend(result.review_messages)
        return list(result.saved_paths)

    @staticmethod
    def _derive_verdict(
        new_method: MethodResult,
        baselines: Sequence[MethodResult],
        report: EvaluationReport,
        *,
        has_reference: bool,
    ) -> None:
        new = new_method.name
        m_new = report.metrics[new]
        base_names = [b.name for b in baselines]

        # 准确性（需要参考解）
        if has_reference and m_new.rmse is not None:
            base_rmse = {b: report.metrics[b].rmse for b in base_names}
            best_base, best_val = min(base_rmse.items(), key=lambda kv: kv[1])
            if m_new.rmse < best_val:
                pct = 100.0 * (best_val - m_new.rmse) / best_val if best_val else 0.0
                report.strengths.append(
                    f"准确性最佳：RMSE={m_new.rmse:.4g}，比最优基线 {best_base} "
                    f"低 {pct:.1f}%"
                )
            else:
                pct = 100.0 * (m_new.rmse - best_val) / best_val if best_val else 0.0
                report.weaknesses.append(
                    f"准确性落后：RMSE={m_new.rmse:.4g}，比最优基线 {best_base} "
                    f"高 {pct:.1f}%"
                )
            if m_new.correlation is not None:
                report.strengths.append(
                    f"与参考解相关系数 {m_new.correlation:.4f}"
                ) if m_new.correlation >= 0.99 else report.weaknesses.append(
                    f"与参考解相关系数仅 {m_new.correlation:.4f}（< 0.99）"
                )

        # 性能（需要所有 runtime）
        runtimes = {m: report.metrics[m].runtime for m in [new, *base_names]}
        if all(v is not None for v in runtimes.values()):
            fastest, fast_val = min(runtimes.items(), key=lambda kv: kv[1])
            if fastest == new:
                second = min((v for k, v in runtimes.items() if k != new), default=fast_val)
                speedup = second / fast_val if fast_val else 1.0
                report.strengths.append(
                    f"速度最快：{fast_val:.3f} s，比次优快 {speedup:.2f}×"
                )
            else:
                slowdown = runtimes[new] / fast_val if fast_val else 1.0
                report.weaknesses.append(
                    f"速度落后：{runtimes[new]:.3f} s，比最快的 {fastest} 慢 {slowdown:.2f}×"
                )

        if not has_reference:
            report.review_messages.append(
                "[INFO] 未提供参考解，无法评估绝对精度；仅给出方法间差异与性能对比"
            )

    @staticmethod
    def _summary_line(
        new_method: MethodResult, baselines: Sequence[MethodResult], report: EvaluationReport
    ) -> str:
        n_strength = len(report.strengths)
        n_weak = len(report.weaknesses)
        return (
            f"Evaluation of '{new_method.name}' vs {len(baselines)} baseline(s): "
            f"{n_strength} strength(s), {n_weak} weakness(es), "
            f"{len(report.saved_paths)} figure(s)."
        )


def _slug(name: str) -> str:
    """方法名 -> 文件夹安全字符串。"""
    return re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower() or "method"
