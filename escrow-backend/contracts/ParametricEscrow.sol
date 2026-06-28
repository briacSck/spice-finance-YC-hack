// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Minimal, self-contained parametric-insurance escrow for the Spice demo.
/// A policy pays a FIXED payout to the insured the instant a settable index
/// (the "oracle") crosses a trigger — no claim, no adjuster. The contract is
/// PRE-FUNDED: it must already hold the payout, which is reserved at policy
/// creation, so settle() can transfer in a single block. Asset is 6-dp USDC.
///
/// Demo use-case: a heatwave policy. trigger = heat index threshold (e.g. 35),
/// settle(indexValue) is fired by the operator with the observed index (e.g. 41).
interface IERC20 {
    function transfer(address to, uint256 a) external returns (bool);
    function transferFrom(address f, address t, uint256 a) external returns (bool);
    function balanceOf(address) external view returns (uint256);
}

contract ParametricEscrow {
    IERC20 public immutable assetToken;   // payout currency (USDC, 6dp)
    address public operator;              // oracle setter / settler (deployer)

    struct Policy {
        address insured;   // receives the payout
        uint256 premium;   // paid by the insured at creation (kept by the pool)
        uint256 trigger;   // index threshold; payout fires when index >= trigger
        uint256 payout;    // fixed amount reserved at creation, paid on trigger
        bool open;         // false once settled (paid or closed unpaid)
        bool paid;         // true if the trigger fired and the payout was sent
    }

    Policy[] public policies;             // policy_id == array index
    uint256 public reserved;              // sum of `payout` across open policies
    uint256 public lastIndex;             // last index value seen by the oracle

    event PolicyTaken(uint256 indexed id, address indexed insured, uint256 premium, uint256 trigger, uint256 payout);
    event Settled(uint256 indexed id, uint256 indexValue, bool paid, uint256 payout);

    modifier onlyOperator() { require(msg.sender == operator, "not operator"); _; }

    constructor(address _asset) {
        assetToken = IERC20(_asset);
        operator = msg.sender;
    }

    function setOperator(address op) external onlyOperator { operator = op; }

    /// Asset the contract holds beyond what is already reserved for open policies.
    function freeLiquidity() public view returns (uint256) {
        return assetToken.balanceOf(address(this)) - reserved;
    }

    /// Create a policy. The contract must already hold enough UNRESERVED asset to
    /// back `payout` (the pre-funding rule) or this reverts. Pulls `premium` from
    /// the insured (needs a prior approve); pass premium == 0 to skip the pull.
    function takePolicy(address insured, uint256 premium, uint256 trigger, uint256 payout)
        external onlyOperator returns (uint256 id)
    {
        require(payout > 0, "payout=0");
        require(freeLiquidity() >= payout, "underfunded: fund the escrow first");
        if (premium > 0) {
            require(assetToken.transferFrom(insured, address(this), premium), "premium transferFrom");
        }
        reserved += payout;
        id = policies.length;
        policies.push(Policy(insured, premium, trigger, payout, true, false));
        emit PolicyTaken(id, insured, premium, trigger, payout);
    }

    /// Set the oracle index and settle a policy in one call (matches the service's
    /// POST /settle {index_value}). If indexValue >= trigger the payout is sent to
    /// the insured immediately; otherwise the policy closes unpaid. Idempotent per
    /// policy: once open == false it cannot be settled again.
    function settle(uint256 id, uint256 indexValue) external onlyOperator {
        Policy storage p = policies[id];
        require(p.open, "policy closed");
        lastIndex = indexValue;
        p.open = false;
        reserved -= p.payout;
        if (indexValue >= p.trigger) {
            p.paid = true;
            require(assetToken.transfer(p.insured, p.payout), "payout transfer");
        }
        emit Settled(id, indexValue, p.paid, p.paid ? p.payout : 0);
    }

    function policyCount() external view returns (uint256) { return policies.length; }

    /// Position read (matches the service's GET /info).
    function info(uint256 id) external view returns (
        address insured, uint256 premium, uint256 trigger, uint256 payout, bool open, bool paid
    ) {
        Policy storage p = policies[id];
        return (p.insured, p.premium, p.trigger, p.payout, p.open, p.paid);
    }
}
