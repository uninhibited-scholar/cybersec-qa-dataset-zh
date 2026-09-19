from phase107_collect_blind import cluster_tunnel_command


def test_cluster_forward_targets_compute_node_loopback_services():
    command = cluster_tunnel_command("zj225", "slurmc.ie.cuhk.edu.hk", "a100-3")
    assert command[:5] == ["ssh", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes"]
    assert "127.0.0.1:18181:a100-3:18081" in command
    assert "127.0.0.1:18182:a100-3:18082" in command
    assert command[-1] == "zj225@slurmc.ie.cuhk.edu.hk"


def test_cluster_forward_ports_can_be_overridden_without_shell_interpolation():
    command = cluster_tunnel_command("zj225", "slurmc.ie.cuhk.edu.hk", "a100-3", 18181, 18182)
    assert "127.0.0.1:18181:a100-3:18181" in command
    assert "127.0.0.1:18182:a100-3:18182" in command
    assert all(";" not in part for part in command)
