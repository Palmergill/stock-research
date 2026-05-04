import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.services import bitcoin_tools


TXID_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")


def answer_chat(message: str, session_id: str | None = None, timezone_name: str | None = None) -> Dict[str, Any]:
    normalized = message.strip().lower()
    session_id = session_id or str(uuid.uuid4())
    tools_used: List[str] = []
    warnings: List[str] = []

    if any(word in normalized for word in ("send bitcoin", "broadcast", "sign transaction", "private key", "seed phrase")):
        return {
            "answer": "I can only inspect public blockchain data. I cannot send bitcoin, sign transactions, broadcast transactions, or handle wallet secrets.",
            "session_id": session_id,
            "tools_used": [],
            "data": {},
            "warnings": [],
        }

    txid_match = TXID_RE.search(message)
    if txid_match:
        data = bitcoin_tools.get_transaction(txid_match.group(0))
        tools_used.append("get_transaction")
        warnings.extend(data.get("warnings", []))
        return {
            "answer": _transaction_answer(data),
            "session_id": session_id,
            "tools_used": tools_used,
            "data": data,
            "warnings": warnings,
        }

    if "fee" in normalized or "mempool" in normalized:
        data = bitcoin_tools.get_mempool_summary()
        tools_used.append("get_mempool_summary")
        warnings.extend(data.get("warnings", []))
        return {
            "answer": _mempool_answer(data),
            "session_id": session_id,
            "tools_used": tools_used,
            "data": data,
            "warnings": warnings,
        }

    if "sync" in normalized or "node" in normalized or "status" in normalized:
        data = bitcoin_tools.get_node_status()
        tools_used.append("get_node_status")
        warnings.extend(data.get("warnings", []))
        return {
            "answer": _status_answer(data),
            "session_id": session_id,
            "tools_used": tools_used,
            "data": data,
            "warnings": warnings,
        }

    if "block" in normalized or "latest" in normalized or "height" in normalized:
        height_match = re.search(r"\b\d{1,7}\b", normalized)
        if height_match and "latest" not in normalized:
            data = bitcoin_tools.get_block(height_match.group(0))
            tools_used.append("get_block")
        else:
            data = bitcoin_tools.get_latest_block()
            tools_used.append("get_latest_block")
        warnings.extend(data.get("warnings", []))
        return {
            "answer": _block_answer(data),
            "session_id": session_id,
            "tools_used": tools_used,
            "data": data,
            "warnings": warnings,
        }

    if "mined" in normalized or "btc" in normalized or "bitcoin" in normalized:
        data = bitcoin_tools.get_latest_block()
        tools_used.append("get_latest_block")
        warnings.extend(data.get("warnings", []))
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        answer = (
            f"For mined-BTC questions I need a block time window. For now, the latest known block is "
            f"{data.get('height')} and its subsidy is {data.get('subsidy_btc')} BTC. "
            f"Use a specific range like 'blocks mined today' next; current v1 defaults date interpretation to UTC ({today})."
        )
        return {
            "answer": answer,
            "session_id": session_id,
            "tools_used": tools_used,
            "data": data,
            "warnings": warnings,
        }

    data = bitcoin_tools.get_latest_block()
    tools_used.append("get_latest_block")
    warnings.extend(data.get("warnings", []))
    return {
        "answer": "I can answer questions about blocks, transactions, node sync, and mempool fees. The latest chain tip I can see is included below.",
        "session_id": session_id,
        "tools_used": tools_used,
        "data": data,
        "warnings": warnings,
    }


def _status_answer(data: Dict[str, Any]) -> str:
    if data.get("error"):
        return data["error"]
    sync = "syncing" if data.get("initial_block_download") else "synced"
    progress = data.get("verification_progress")
    progress_text = f" Verification progress is {progress:.4%}." if isinstance(progress, float) else ""
    return f"The Bitcoin node is on {data.get('chain')} at height {data.get('blocks')} and appears {sync}.{progress_text}"


def _block_answer(data: Dict[str, Any]) -> str:
    if data.get("error"):
        return data["error"]
    return (
        f"Block {data.get('height')} has {data.get('tx_count')} transactions, "
        f"weight {data.get('weight')}, and a {data.get('subsidy_btc')} BTC subsidy. "
        f"It was timestamped {data.get('time')}."
    )


def _mempool_answer(data: Dict[str, Any]) -> str:
    if data.get("error"):
        return data["error"]
    estimates = data.get("fee_estimates_sats_vb", {})
    fast = estimates.get("2")
    medium = estimates.get("6")
    return (
        f"The mempool currently has about {data.get('tx_count')} transactions. "
        f"Estimated fees are {fast} sats/vB for roughly 2 blocks and {medium} sats/vB for roughly 6 blocks."
    )


def _transaction_answer(data: Dict[str, Any]) -> str:
    if data.get("error"):
        return data["error"]
    status = "confirmed" if data.get("confirmed") else "unconfirmed"
    fee_text = f"The fee was {data.get('fee_btc')} BTC." if data.get("fee_available") else "Exact fee is not available from this lookup yet."
    return (
        f"That transaction is {status} with {data.get('confirmations', 0)} confirmations. "
        f"It has {data.get('input_count')} inputs and {data.get('output_count')} outputs totaling {data.get('total_output_btc')} BTC. "
        f"{fee_text}"
    )
