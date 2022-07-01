defmodule Hello do
  def hello do
    IO.puts("Hello world!!")
  end

  def hello(world) do
    str = "Hello" <> world
    IO.puts(str)
  end
end
