library(ggplot2)
library(scales)
library(patchwork)

# colors: #E69F00, #56B4E9, #009E73, #F0E442, #0072B2, #D55E00, #CC79A7
colors <- list(
    color0 = "#E69F00",
    color1 = "#56B4E9",
    color2 = "#25b28c",
    color3 = "#F0E442",
    color5 = "#D55E00",
    color6 = "#CC79A7",
    color4 = "#0072B2"
)

# --------------------------
# Top plot: enforceability
# --------------------------
df1 <- data.frame(
  Benchmark = rep(c("tau2-Bench", "CAR-bench", "MedAgentBench"), each = 3),
  Category = rep(c("Out of Scope", "Not Enforceable", "Enforceable"), times = 3),
  Value = c(
    69, 9, 42,
    0, 1, 17,
    31, 23, 34
  )
)

df1$Benchmark <- factor(
  df1$Benchmark,
  levels = c("tau2-Bench", "CAR-bench", "MedAgentBench")
)

df1 <- do.call(rbind, lapply(split(df1, df1$Benchmark), function(d) {
  d$Prop <- d$Value / sum(d$Value)
  d$Label <- ifelse(
    d$Prop >= 0.08,
    paste0(d$Value, " (", round(100 * d$Prop, 1), "%)"),
    ""
  )
  d
}))

df1$Category <- factor(
  df1$Category,
  levels = c("Not Enforceable", "Enforceable", "Out of Scope")
)

colors1 <- c( # red blue green
  "Out of Scope" = colors[[1]],
  "Not Enforceable" = colors[[2]],
  "Enforceable"  = colors[[3]]
)

p1 <- ggplot(df1, aes(x = Benchmark, y = Prop, fill = Category)) +
  geom_col(width = 0.7, color = "white", linewidth = 0.8) +
  geom_text(
    aes(label = Label),
    position = position_stack(vjust = 0.5),
    size = 4.5,
    family = "serif"
  ) +
  scale_fill_manual(values = colors1) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    expand = c(0, 0)
  ) +
  scale_x_discrete(
    labels = c(
      "tau2-Bench" = expression(tau^2 * "-Bench"),
      "CAR-bench" = "CAR-bench",
      "MedAgentBench" = "MedAgentBench"
    )
  ) +
  labs(x = NULL, y = "Share", fill = NULL) +
  theme_classic(base_size = 14, base_family = "serif") +
  theme(
    axis.text.x = element_text(size = 14, face = "bold"),
    axis.text.y = element_text(size = 14),
    axis.title.y = element_text(size = 14),
    legend.position = "right",
    legend.text = element_text(size = 14),
    panel.border = element_blank()
  )


ggsave("stacked_bar_benchmarks_enforceability.pdf", p1, width = 8, height = 2, bg = "white")

# --------------------------
# Bottom plot: guardrail types
# --------------------------
df2 <- data.frame(
  Benchmark = rep(c("tau2-Bench", "CAR-bench", "MedAgentBench"), each = 7),
  Category = rep(c(
    "User Confirmation",
    "Schema Constraint",
    "Response Template",
    "API Validation",
    "Information Flow",
    "Temporal Logic",
    "Combination of Guardrails"
  ), times = 3),
  Value = c(
    1, 6, 1, 34, 0, 0, 0,   # tau2-Bench
    3, 0, 2, 11, 0, 0, 1,   # CAR-bench
    5, 2, 6, 16, 3, 2, 0    # MedAgentBench
  )
)

df2$Benchmark <- factor(
  df2$Benchmark,
  levels = c("tau2-Bench", "CAR-bench", "MedAgentBench")
)

df2$Category <- factor(
  df2$Category,
  levels = c(
    "API Validation",
    "Schema Constraint",
    "Temporal Logic",
    "Information Flow",
    "User Confirmation",
    "Response Template",
    "Combination of Guardrails"
  )
)

df2 <- do.call(rbind, lapply(split(df2, df2$Benchmark), function(d) {
  d$Prop <- d$Value / sum(d$Value)
  d$Label <- ifelse(
    d$Prop >= 0.08,
    paste0(d$Value, " (", round(100 * d$Prop, 1), "%)"),
    ""
  )
  d
}))

colors2 <- c(
  "API Validation" = colors[[1]],
    "Schema Constraint" = colors[[2]],
    "Temporal Logic" = colors[[3]],
    "Information Flow" = colors[[4]],
    "User Confirmation" = colors[[5]],
    "Response Template" = colors[[6]],
    "Combination of Guardrails" = colors[[7]]
)

p2 <- ggplot(df2, aes(x = Benchmark, y = Prop, fill = Category)) +
  geom_col(width = 0.7, color = "white", linewidth = 0.8) +
  geom_text(
    aes(label = Label),
    position = position_stack(vjust = 0.5),
    size = 4.5,
    family = "serif"
  ) +
  scale_fill_manual(values = colors2) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    expand = c(0, 0)
  ) +
  scale_x_discrete(
    labels = c(
      "tau2-Bench" = expression(tau^2 * "-Bench"),
      "CAR-bench" = "CAR-bench",
      "MedAgentBench" = "MedAgentBench"
    )
  ) +
#   guides(fill = guide_legend(nrow = 3, byrow = TRUE)) +
  labs(x = NULL, y = "Share", fill = NULL) +
  theme_classic(base_size = 14, base_family = "serif") +
  theme(
    axis.text.x = element_text(size = 14, face = "bold"),
    axis.text.y = element_text(size = 14),
    axis.title.y = element_text(size = 14),
    legend.position = "right",
    legend.text = element_text(size = 14),
    panel.border = element_blank()
  )

# --------------------------
# Combine vertically
# --------------------------
p <- p1 / p2 + plot_layout(heights = c(1, 1))

print(p)

# p2
ggsave("stacked_bar_benchmarks_guardrail_types.pdf", p2, width = 8, height = 3, bg = "white")

ggsave("stacked_bar_benchmarks_two_panels.pdf", p, width = 8, height = 6, bg = "white")