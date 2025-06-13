## Advanced Patterns



### ​Environment-Specific Evaluation


Copy```python
<span style="color:#6E7781;--shiki-dark:#6A9955"># Browser-specific evaluation</span>
<span style="color:#CF222E;--shiki-dark:#C586C0">if</span><span style="color:#1F2328;--shiki-dark:#f3f7f6"> task.gym </span><span style="color:#CF222E;--shiki-dark:#f3f7f6">==</span><span style="color:#0A3069;--shiki-dark:#CE9178"> "hud-browser"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">:</span>
<span style="color:#1F2328;--shiki-dark:#f3f7f6">    evaluate</span><span style="color:#CF222E;--shiki-dark:#f3f7f6">=</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">(</span><span style="color:#0A3069;--shiki-dark:#CE9178">"element_exists"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">, </span><span style="color:#0A3069;--shiki-dark:#CE9178">".success-indicator"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">)</span>

<span style="color:#6E7781;--shiki-dark:#6A9955"># Response-only evaluation  </span>
<span style="color:#CF222E;--shiki-dark:#C586C0">if</span><span style="color:#1F2328;--shiki-dark:#f3f7f6"> task.gym </span><span style="color:#CF222E;--shiki-dark:#f3f7f6">==</span><span style="color:#0A3069;--shiki-dark:#CE9178"> "qa"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">:</span>
<span style="color:#1F2328;--shiki-dark:#f3f7f6">    evaluate</span><span style="color:#CF222E;--shiki-dark:#f3f7f6">=</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">(</span><span style="color:#0A3069;--shiki-dark:#CE9178">"response_includes"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">, </span><span style="color:#0A3069;--shiki-dark:#CE9178">"expected_answer"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">)</span>
```


### ​Dynamic Task Generation


Copy```python
<span style="color:#CF222E;--shiki-dark:#9cdcfe">def</span><span style="color:#8250DF;--shiki-dark:#DCDCAA"> create_search_task</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">(</span><span style="color:#1F2328;--shiki-dark:#9CDCFE">query</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">, </span><span style="color:#1F2328;--shiki-dark:#9CDCFE">expected_result</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">):</span>
<span style="color:#CF222E;--shiki-dark:#C586C0">    return</span><span style="color:#1F2328;--shiki-dark:#f3f7f6"> Task(</span>
<span style="color:#953800;--shiki-dark:#9CDCFE">        prompt</span><span style="color:#CF222E;--shiki-dark:#f3f7f6">=</span><span style="color:#CF222E;--shiki-dark:#9cdcfe">f</span><span style="color:#0A3069;--shiki-dark:#CE9178">"Search for '</span><span style="color:#CF222E;--shiki-dark:#9cdcfe">{</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">query</span><span style="color:#CF222E;--shiki-dark:#9cdcfe">}</span><span style="color:#0A3069;--shiki-dark:#CE9178">' and find information about it"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">,</span>
<span style="color:#953800;--shiki-dark:#9CDCFE">        gym</span><span style="color:#CF222E;--shiki-dark:#f3f7f6">=</span><span style="color:#0A3069;--shiki-dark:#CE9178">"hud-browser"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">,</span>
<span style="color:#953800;--shiki-dark:#9CDCFE">        setup</span><span style="color:#CF222E;--shiki-dark:#f3f7f6">=</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">(</span><span style="color:#0A3069;--shiki-dark:#CE9178">"goto"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">, </span><span style="color:#0A3069;--shiki-dark:#CE9178">"google.com"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">),</span>
<span style="color:#953800;--shiki-dark:#9CDCFE">        evaluate</span><span style="color:#CF222E;--shiki-dark:#f3f7f6">=</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">(</span><span style="color:#0A3069;--shiki-dark:#CE9178">"response_includes"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">, expected_result)</span>
<span style="color:#1F2328;--shiki-dark:#f3f7f6">    )</span>

<span style="color:#1F2328;--shiki-dark:#f3f7f6">task </span><span style="color:#CF222E;--shiki-dark:#f3f7f6">=</span><span style="color:#1F2328;--shiki-dark:#f3f7f6"> create_search_task(</span><span style="color:#0A3069;--shiki-dark:#CE9178">"artificial intelligence"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">, </span><span style="color:#0A3069;--shiki-dark:#CE9178">"machine learning"</span><span style="color:#1F2328;--shiki-dark:#f3f7f6">)</span>
```