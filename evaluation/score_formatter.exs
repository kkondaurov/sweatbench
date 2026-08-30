defmodule GroupStay.TestReportFormatter do
  @moduledoc false

  use GenServer

  @impl true
  def init(_options) do
    {:ok, %{tests: []}}
  end

  @impl true
  def handle_cast({:test_finished, test}, state) do
    result = %{
      id: "#{inspect(test.module)}::#{test.name}",
      module: inspect(test.module),
      name: Atom.to_string(test.name),
      status: status(test.state),
      time_us: test.time
    }

    {:noreply, %{state | tests: [result | state.tests]}}
  end

  def handle_cast({:suite_finished, times_us}, state) do
    output = System.fetch_env!("GROUP_STAY_TEST_RESULT_PATH")

    report = %{
      times_us: times_us,
      tests: Enum.reverse(state.tests)
    }

    File.write!(output, Jason.encode!(report))
    {:noreply, state}
  end

  def handle_cast(_event, state), do: {:noreply, state}

  defp status(nil), do: "passed"
  defp status({:failed, _failures}), do: "failed"
  defp status({:invalid, _module}), do: "invalid"
  defp status({:excluded, _reason}), do: "excluded"
  defp status({:skipped, _reason}), do: "skipped"
  defp status(_state), do: "failed"
end
